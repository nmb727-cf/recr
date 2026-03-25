import base64
import json
import logging
import urllib.parse
from dataclasses import dataclass
from datetime import timedelta
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders as email_encoders
from urllib import request as urlrequest
from urllib.error import HTTPError

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone

from apps.communications.email_dispatch.types import SendResult
from apps.communications.models import EmailSendingAccount
from apps.communications.utils import decrypt_json, decrypt_string, encrypt_json

logger = logging.getLogger(__name__)


@dataclass
class OAuthConnectResult:
    auth_url: str
    state: str


class BaseEmailProvider:
    key = 'base'

    def connect(self, *, state: str, redirect_uri: str) -> OAuthConnectResult:
        raise NotImplementedError

    def refresh_credentials(self, account: EmailSendingAccount) -> bool:
        raise NotImplementedError

    def validate_connection(self, account: EmailSendingAccount) -> bool:
        return account.status == 'connected' and account.can_send and not account.deleted_at

    def send_email(self, *, account: EmailSendingAccount | None, from_email: str, from_name: str, reply_to: str, recipients: list[str], subject: str, body_text: str, body_html: str, attachments: list[dict] | None = None) -> SendResult:
        raise NotImplementedError

    def disconnect(self, account: EmailSendingAccount) -> None:
        account.status = 'disconnected'
        account.health_status = 'unknown'
        account.save(update_fields=['status', 'health_status', 'updated_at'])

    def get_health_status(self, account: EmailSendingAccount) -> str:
        if account.deleted_at:
            return 'unhealthy'
        if account.status in ('error', 'expired', 'disconnected'):
            return 'degraded'
        if account.status == 'connected' and account.can_send:
            return 'healthy'
        return 'unknown'


class SMTPProvider(BaseEmailProvider):
    key = 'smtp'

    def refresh_credentials(self, account: EmailSendingAccount) -> bool:
        return True

    def send_email(self, *, account: EmailSendingAccount | None, from_email: str, from_name: str, reply_to: str, recipients: list[str], subject: str, body_text: str, body_html: str, attachments: list[dict] | None = None) -> SendResult:
        try:
            if not account:
                return SendResult(ok=False, status='failed', error='SMTP account missing')
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=account.smtp_host,
                port=account.smtp_port,
                username=account.smtp_username,
                password=decrypt_string(account.smtp_password_encrypted),
                use_tls=(account.smtp_encryption_mode == 'tls'),
                use_ssl=(account.smtp_encryption_mode == 'ssl'),
            )
            rendered_from = f'{from_name} <{from_email}>' if from_name else from_email
            email = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=rendered_from,
                to=recipients,
                reply_to=[reply_to] if reply_to else None,
                connection=connection,
            )
            if body_html:
                email.attach_alternative(body_html, 'text/html')
            for attachment in attachments or []:
                email.attach(attachment.get('filename', 'attachment'), attachment.get('content', b''), attachment.get('mime_type', 'application/octet-stream'))
            email.send()
            return SendResult(ok=True, status='sent')
        except Exception as exc:
            logger.exception('SMTP send failed')
            return SendResult(ok=False, status='failed', error=str(exc))


class SystemEmailProvider(BaseEmailProvider):
    key = 'system'

    def refresh_credentials(self, account: EmailSendingAccount) -> bool:
        return True

    def send_email(self, *, account: EmailSendingAccount | None, from_email: str, from_name: str, reply_to: str, recipients: list[str], subject: str, body_text: str, body_html: str, attachments: list[dict] | None = None) -> SendResult:
        try:
            sender_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@talentos.com')
            rendered_from = f'{from_name} <{sender_email}>' if from_name else sender_email
            email = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=rendered_from,
                to=recipients,
                reply_to=[reply_to] if reply_to else None,
            )
            if body_html:
                email.attach_alternative(body_html, 'text/html')
            for attachment in attachments or []:
                email.attach(attachment.get('filename', 'attachment'), attachment.get('content', b''), attachment.get('mime_type', 'application/octet-stream'))
            email.send()
            return SendResult(ok=True, status='sent')
        except Exception as exc:
            logger.exception('System send failed')
            return SendResult(ok=False, status='failed', error=str(exc))


def _build_mime_message(*, from_email: str, from_name: str, recipients: list[str], subject: str, body_text: str, body_html: str, reply_to: str, attachments: list[dict]) -> MIMEMultipart | MIMEText:
    """Build a MIME email message suitable for base64-encoding (Gmail) or inspection."""
    if body_html and attachments:
        outer = MIMEMultipart('mixed')
        alt = MIMEMultipart('alternative')
        alt.attach(MIMEText(body_text or '', 'plain', 'utf-8'))
        alt.attach(MIMEText(body_html, 'html', 'utf-8'))
        outer.attach(alt)
    elif body_html:
        outer = MIMEMultipart('alternative')
        outer.attach(MIMEText(body_text or '', 'plain', 'utf-8'))
        outer.attach(MIMEText(body_html, 'html', 'utf-8'))
    elif attachments:
        outer = MIMEMultipart('mixed')
        outer.attach(MIMEText(body_text or '', 'plain', 'utf-8'))
    else:
        outer = MIMEText(body_text or '', 'plain', 'utf-8')

    sender = f'{from_name} <{from_email}>' if from_name else from_email
    outer['From'] = sender
    outer['To'] = ', '.join(recipients)
    outer['Subject'] = subject
    if reply_to:
        outer['Reply-To'] = reply_to

    for att in attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(att.get('content', b''))
        email_encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename=att.get('filename', 'attachment'))
        if isinstance(outer, MIMEMultipart):
            outer.attach(part)

    return outer


def _json_api_request(url: str, *, method: str = 'GET', token: str, payload: dict | None = None) -> dict:
    """Make a JSON API call with a Bearer token. Raises HTTPError on non-2xx."""
    data = json.dumps(payload).encode() if payload is not None else None
    req = urlrequest.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        method=method,
    )
    with urlrequest.urlopen(req, timeout=30) as resp:
        body = resp.read()
        return json.loads(body) if body else {}


class OAuthProviderMixin(BaseEmailProvider):
    auth_base_url = ''
    token_url = ''
    client_id_setting = ''
    client_secret_setting = ''
    scope = ''

    def _client_id(self):
        return str(getattr(settings, self.client_id_setting, '') or '').strip()

    def _client_secret(self):
        return str(getattr(settings, self.client_secret_setting, '') or '').strip()

    def connect(self, *, state: str, redirect_uri: str) -> OAuthConnectResult:
        params = self.build_auth_params(state=state, redirect_uri=redirect_uri)
        return OAuthConnectResult(auth_url=f'{self.auth_base_url}?{urllib.parse.urlencode(params)}', state=state)

    def build_auth_params(self, *, state: str, redirect_uri: str) -> dict:
        return {
            'client_id': self._client_id(),
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': self.scope,
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent',
        }

    def exchange_code(self, *, code: str, redirect_uri: str) -> dict:
        payload = self.build_token_payload(code=code, redirect_uri=redirect_uri)
        req = urlrequest.Request(
            self.token_url,
            data=urllib.parse.urlencode(payload).encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST',
        )
        try:
            with urlrequest.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            raw_error = ''
            try:
                raw_error = exc.read().decode()
            except Exception:
                raw_error = ''

            provider_error = ''
            provider_description = ''
            if raw_error:
                try:
                    parsed = json.loads(raw_error)
                    provider_error = str(parsed.get('error') or '')
                    provider_description = str(
                        parsed.get('error_description')
                        or parsed.get('error_description_detail')
                        or parsed.get('message')
                        or ''
                    )
                except Exception:
                    provider_description = raw_error[:300]

            logger.error(
                'OAuth code exchange failed: provider=%s status=%s error=%s description=%s',
                self.key,
                exc.code,
                provider_error or 'unknown',
                provider_description or 'n/a',
            )
            reason = provider_error or f'http_{exc.code}'
            detail = provider_description or 'Token exchange failed'
            raise ValueError(f'{reason}: {detail}') from exc

    def build_token_payload(self, *, code: str, redirect_uri: str) -> dict:
        return {
            'code': code,
            'client_id': self._client_id(),
            'client_secret': self._client_secret(),
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }

    def refresh_credentials(self, account: EmailSendingAccount) -> bool:
        token_data = decrypt_json(account.refresh_token_encrypted)
        refresh_token = token_data.get('refresh_token')
        if not refresh_token:
            return False
        payload = self.build_refresh_payload(refresh_token)
        req = urlrequest.Request(
            self.token_url,
            data=urllib.parse.urlencode(payload).encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST',
        )
        try:
            with urlrequest.urlopen(req, timeout=15) as response:
                response_payload = json.loads(response.read().decode())
        except Exception:
            logger.exception('OAuth refresh failed')
            return False

        access_token = response_payload.get('access_token')
        if not access_token:
            return False

        account.access_token_encrypted = encrypt_json({'access_token': access_token})
        next_refresh = response_payload.get('refresh_token') or refresh_token
        account.refresh_token_encrypted = encrypt_json({'refresh_token': next_refresh})
        account.token_expires_at = timezone.now() + timedelta(seconds=int(response_payload.get('expires_in', 3600)))
        account.status = 'connected'
        account.health_status = 'healthy'
        account.last_success_at = timezone.now()
        account.failure_reason = ''
        account.save(update_fields=['access_token_encrypted', 'refresh_token_encrypted', 'token_expires_at', 'status', 'health_status', 'last_success_at', 'failure_reason', 'updated_at'])
        return True

    def build_refresh_payload(self, refresh_token: str) -> dict:
        return {
            'client_id': self._client_id(),
            'client_secret': self._client_secret(),
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }

    def _get_access_token(self, account: EmailSendingAccount) -> str | None:
        """Return a valid access token, refreshing proactively if within 5 minutes of expiry."""
        token_data = decrypt_json(account.access_token_encrypted)
        access_token = token_data.get('access_token', '')

        if account.token_expires_at:
            if timezone.now() >= account.token_expires_at - timedelta(minutes=5):
                if self.refresh_credentials(account):
                    token_data = decrypt_json(account.access_token_encrypted)
                    access_token = token_data.get('access_token', '')

        return access_token or None

    def fetch_user_info(self, access_token: str) -> dict:
        """
        Fetch the authenticated user's identity from the provider.
        Returns at minimum {'email': str, 'name': str}.
        Override in subclasses.
        """
        raise NotImplementedError

    def fetch_user_email(self, access_token: str) -> str:
        """Convenience wrapper kept for backward compat."""
        return self.fetch_user_info(access_token).get('email', '')


class GmailOAuthProvider(OAuthProviderMixin):
    key = 'gmail_oauth'
    auth_base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
    token_url = 'https://oauth2.googleapis.com/token'
    client_id_setting = 'GOOGLE_OAUTH_CLIENT_ID'
    client_secret_setting = 'GOOGLE_OAUTH_CLIENT_SECRET'
    redirect_uri_setting = 'GOOGLE_OAUTH_REDIRECT_URI'
    scope = 'openid email profile https://www.googleapis.com/auth/gmail.send'

    USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
    GMAIL_SEND_URL = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'

    def _redirect_uri(self) -> str:
        return getattr(settings, self.redirect_uri_setting, '')

    def build_auth_params(self, *, state: str, redirect_uri: str) -> dict:
        # Always use the server-side configured URI — never trust caller-supplied value.
        return {
            'client_id': self._client_id(),
            'redirect_uri': self._redirect_uri(),
            'response_type': 'code',
            'scope': self.scope,
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent',
        }

    def fetch_user_info(self, access_token: str) -> dict:
        try:
            data = _json_api_request(self.USERINFO_URL, token=access_token)
            return {
                'email': data.get('email', ''),
                'name': data.get('name', '') or data.get('given_name', ''),
            }
        except HTTPError as exc:
            raw_error = ''
            try:
                raw_error = exc.read().decode()
            except Exception:
                raw_error = ''
            logger.error(
                'Gmail userinfo fetch failed: status=%s body=%s',
                exc.code,
                raw_error[:300],
            )
            raise ValueError(f'gmail_userinfo_failed_http_{exc.code}') from exc
        except Exception as exc:
            logger.exception('Gmail userinfo fetch failed')
            raise ValueError(f'gmail_userinfo_failed: {exc}') from exc

    def validate_connection(self, account: EmailSendingAccount) -> bool:
        try:
            access_token = self._get_access_token(account)
            if not access_token:
                return False
            _json_api_request(self.USERINFO_URL, token=access_token)
            return True
        except Exception:
            return False

    def send_email(self, *, account: EmailSendingAccount | None, from_email: str, from_name: str, reply_to: str, recipients: list[str], subject: str, body_text: str, body_html: str, attachments: list[dict] | None = None) -> SendResult:
        if not account:
            return SendResult(ok=False, status='failed', error='Gmail account missing')
        try:
            access_token = self._get_access_token(account)
            if not access_token:
                return SendResult(ok=False, status='failed', error='No valid Gmail access token — please reconnect your account')

            mime_msg = _build_mime_message(
                from_email=from_email,
                from_name=from_name,
                recipients=recipients,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                reply_to=reply_to,
                attachments=attachments or [],
            )
            raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()

            try:
                _json_api_request(
                    self.GMAIL_SEND_URL,
                    method='POST',
                    token=access_token,
                    payload={'raw': raw},
                )
            except HTTPError as exc:
                if exc.code == 401:
                    # Token invalid — attempt one refresh then retry
                    if self.refresh_credentials(account):
                        access_token = self._get_access_token(account)
                        _json_api_request(
                            self.GMAIL_SEND_URL,
                            method='POST',
                            token=access_token,
                            payload={'raw': raw},
                        )
                    else:
                        raise

            account.last_success_at = timezone.now()
            account.save(update_fields=['last_success_at', 'updated_at'])
            return SendResult(ok=True, status='sent')
        except Exception as exc:
            logger.exception('Gmail API send failed')
            return SendResult(ok=False, status='failed', error=str(exc))


class MicrosoftOAuthProvider(OAuthProviderMixin):
    key = 'microsoft_oauth'
    auth_base_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
    token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    client_id_setting = 'MICROSOFT_OAUTH_CLIENT_ID'
    client_secret_setting = 'MICROSOFT_OAUTH_CLIENT_SECRET'
    redirect_uri_setting = 'MICROSOFT_OAUTH_REDIRECT_URI'
    scope = 'offline_access https://graph.microsoft.com/Mail.Send User.Read'

    GRAPH_ME_URL = 'https://graph.microsoft.com/v1.0/me'
    GRAPH_SEND_URL = 'https://graph.microsoft.com/v1.0/me/sendMail'

    def _redirect_uri(self) -> str:
        return getattr(settings, self.redirect_uri_setting, '')

    def build_auth_params(self, *, state: str, redirect_uri: str) -> dict:
        # Always use the server-side configured URI — never trust caller-supplied value.
        return {
            'client_id': self._client_id(),
            'redirect_uri': self._redirect_uri(),
            'response_type': 'code',
            'response_mode': 'query',
            'scope': self.scope,
            'state': state,
            'prompt': 'consent',
        }

    def fetch_user_info(self, access_token: str) -> dict:
        try:
            data = _json_api_request(self.GRAPH_ME_URL, token=access_token)
            return {
                'email': data.get('mail') or data.get('userPrincipalName', ''),
                'name': data.get('displayName', ''),
            }
        except HTTPError as exc:
            raw_error = ''
            try:
                raw_error = exc.read().decode()
            except Exception:
                raw_error = ''
            logger.error(
                'Microsoft Graph me-fetch failed: status=%s body=%s',
                exc.code,
                raw_error[:300],
            )
            raise ValueError(f'microsoft_userinfo_failed_http_{exc.code}') from exc
        except Exception as exc:
            logger.exception('Microsoft Graph me-fetch failed')
            raise ValueError(f'microsoft_userinfo_failed: {exc}') from exc

    def validate_connection(self, account: EmailSendingAccount) -> bool:
        try:
            access_token = self._get_access_token(account)
            if not access_token:
                return False
            _json_api_request(self.GRAPH_ME_URL, token=access_token)
            return True
        except Exception:
            return False

    def _build_graph_message(self, *, from_email: str, from_name: str, recipients: list[str], subject: str, body_text: str, body_html: str, reply_to: str, attachments: list[dict]) -> dict:
        message: dict = {
            'subject': subject,
            'body': {
                'contentType': 'HTML' if body_html else 'Text',
                'content': body_html or body_text or '',
            },
            'toRecipients': [{'emailAddress': {'address': r}} for r in recipients],
        }

        if reply_to:
            message['replyTo'] = [{'emailAddress': {'address': reply_to}}]

        if from_email:
            sender_name = from_name or from_email
            message['from'] = {'emailAddress': {'name': sender_name, 'address': from_email}}

        if attachments:
            message['attachments'] = [
                {
                    '@odata.type': '#microsoft.graph.fileAttachment',
                    'name': att.get('filename', 'attachment'),
                    'contentBytes': base64.b64encode(att.get('content', b'')).decode(),
                    'contentType': att.get('mime_type', 'application/octet-stream'),
                }
                for att in attachments
            ]

        return message

    def send_email(self, *, account: EmailSendingAccount | None, from_email: str, from_name: str, reply_to: str, recipients: list[str], subject: str, body_text: str, body_html: str, attachments: list[dict] | None = None) -> SendResult:
        if not account:
            return SendResult(ok=False, status='failed', error='Microsoft account missing')
        try:
            access_token = self._get_access_token(account)
            if not access_token:
                return SendResult(ok=False, status='failed', error='No valid Microsoft access token — please reconnect your account')

            graph_message = self._build_graph_message(
                from_email=from_email,
                from_name=from_name,
                recipients=recipients,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                reply_to=reply_to,
                attachments=attachments or [],
            )

            try:
                _json_api_request(
                    self.GRAPH_SEND_URL,
                    method='POST',
                    token=access_token,
                    payload={'message': graph_message, 'saveToSentItems': True},
                )
            except HTTPError as exc:
                if exc.code == 401:
                    if self.refresh_credentials(account):
                        access_token = self._get_access_token(account)
                        _json_api_request(
                            self.GRAPH_SEND_URL,
                            method='POST',
                            token=access_token,
                            payload={'message': graph_message, 'saveToSentItems': True},
                        )
                    else:
                        raise

            account.last_success_at = timezone.now()
            account.save(update_fields=['last_success_at', 'updated_at'])
            return SendResult(ok=True, status='sent')
        except Exception as exc:
            logger.exception('Microsoft Graph send failed')
            return SendResult(ok=False, status='failed', error=str(exc))


def get_provider(provider_type: str) -> BaseEmailProvider:
    mapping = {
        'system': SystemEmailProvider,
        'gmail_oauth': GmailOAuthProvider,
        'microsoft_oauth': MicrosoftOAuthProvider,
        'smtp': SMTPProvider,
    }
    provider_cls = mapping.get(provider_type, SystemEmailProvider)
    return provider_cls()
