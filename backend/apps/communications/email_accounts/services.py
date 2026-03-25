import secrets
import uuid
import logging
from dataclasses import dataclass
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from apps.communications.email_accounts.providers import get_provider
from apps.communications.models import (
    EmailAccountPermission,
    EmailAccountStatus,
    EmailHealthStatus,
    EmailPreference,
    EmailProviderType,
    EmailSendingAccount,
)
from apps.communications.utils import encrypt_json, encrypt_string

OAUTH_STATE_CACHE_PREFIX = 'comm_email_oauth_state'
OAUTH_STATE_TTL_SECONDS = 900
logger = logging.getLogger(__name__)


@dataclass
class OAuthStateData:
    tenant_id: str
    user_id: str
    provider_type: str


class UserEmailAccountManager:
    @staticmethod
    def ensure_system_account(*, tenant_id: str) -> EmailSendingAccount:
        account, _ = EmailSendingAccount.objects.get_or_create(
            tenant_id=tenant_id,
            user_id=None,
            provider_type=EmailProviderType.SYSTEM,
            account_scope='system',
            email_address='notifications@talentos.com',
            defaults={
                'display_name': 'TalentOS Notifications',
                'from_name': 'TalentOS Notifications',
                'status': EmailAccountStatus.CONNECTED,
                'can_send': True,
                'can_receive': False,
                'health_status': EmailHealthStatus.HEALTHY,
            },
        )
        return account

    @staticmethod
    def get_accessible_accounts(*, tenant_id: str, user_id: str):
        UserEmailAccountManager.ensure_system_account(tenant_id=tenant_id)
        qs = EmailSendingAccount.objects.filter(tenant_id=tenant_id, deleted_at__isnull=True)
        return qs.filter(
            Q(user_id=user_id) |
            Q(account_scope='tenant_shared', permissions__user_id=user_id, permissions__can_send=True) |
            Q(provider_type='system')
        ).distinct()

    @staticmethod
    def set_default_account(*, tenant_id: str, user_id: str, account: EmailSendingAccount):
        EmailSendingAccount.objects.filter(tenant_id=tenant_id, user_id=user_id, is_default_sender=True).exclude(id=account.id).update(is_default_sender=False)
        account.is_default_sender = True
        account.save(update_fields=['is_default_sender', 'updated_at'])

        pref, _ = EmailPreference.objects.get_or_create(
            tenant_id=tenant_id,
            user_id=user_id,
            defaults={'allow_system_fallback': True},
        )
        pref.default_sender_account = account
        pref.save(update_fields=['default_sender_account', 'updated_at'])

    @staticmethod
    def create_smtp_account(*, tenant_id: str, user_id: str, data: dict) -> EmailSendingAccount:
        account = EmailSendingAccount.objects.create(
            tenant_id=tenant_id,
            user_id=user_id,
            provider_type=EmailProviderType.SMTP,
            account_scope=data.get('account_scope', 'user'),
            email_address=data['email_address'],
            display_name=data.get('display_name', ''),
            from_name=data.get('from_name', ''),
            status=EmailAccountStatus.PENDING,
            can_send=True,
            can_receive=False,
            smtp_host=data.get('smtp_host', ''),
            smtp_port=data.get('smtp_port'),
            smtp_username=data.get('smtp_username', ''),
            smtp_password_encrypted=encrypt_string(data.get('smtp_password', '')),
            smtp_encryption_mode=data.get('smtp_encryption_mode', 'tls'),
            signature_html=data.get('signature_html', ''),
            signature_text=data.get('signature_text', ''),
            metadata_json=data.get('metadata_json', {}),
        )
        return account

    @staticmethod
    def build_oauth_state(*, tenant_id: str, user_id: str, provider_type: str) -> str:
        state = secrets.token_urlsafe(32)
        cache.set(
            f'{OAUTH_STATE_CACHE_PREFIX}:{state}',
            {
                'tenant_id': str(tenant_id),
                'user_id': str(user_id),
                'provider_type': provider_type,
            },
            OAUTH_STATE_TTL_SECONDS,
        )
        return state

    @staticmethod
    def consume_oauth_state(state: str) -> OAuthStateData | None:
        key = f'{OAUTH_STATE_CACHE_PREFIX}:{state}'
        data = cache.get(key)
        if not data:
            return None
        cache.delete(key)
        return OAuthStateData(**data)

    @staticmethod
    def initiate_oauth(*, tenant_id: str, user_id: str, provider_type: str, redirect_uri: str) -> dict:
        logger.info(
            'OAuth initiate requested: provider=%s tenant_id=%s user_id=%s redirect_uri=%s',
            provider_type,
            tenant_id,
            user_id,
            redirect_uri,
        )
        state = UserEmailAccountManager.build_oauth_state(
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            provider_type=provider_type,
        )
        provider = get_provider(provider_type)
        connect = provider.connect(state=state, redirect_uri=redirect_uri)
        logger.info(
            'OAuth initiate built: provider=%s state_prefix=%s auth_url_generated=%s',
            provider_type,
            state[:8],
            bool(connect.auth_url),
        )
        return {'auth_url': connect.auth_url, 'state': connect.state}

    @staticmethod
    def complete_oauth(*, state: str, code: str, redirect_uri: str) -> EmailSendingAccount:
        """
        Exchange an OAuth authorisation code for tokens and create/update an
        EmailSendingAccount. The redirect_uri must be the provider-registered
        backend callback URL (from Django settings), NOT a frontend URL.
        """
        logger.info(
            'OAuth callback processing started: state_prefix=%s redirect_uri=%s',
            state[:8] if state else '',
            redirect_uri,
        )
        state_data = UserEmailAccountManager.consume_oauth_state(state)
        if not state_data:
            logger.warning('OAuth state validation failed: state_prefix=%s', state[:8] if state else '')
            raise ValueError('Invalid or expired OAuth state. Please try connecting again.')
        logger.info(
            'OAuth state validation passed: provider=%s tenant_id=%s user_id=%s',
            state_data.provider_type,
            state_data.tenant_id,
            state_data.user_id,
        )

        provider = get_provider(state_data.provider_type)
        logger.info(
            'OAuth token exchange starting: provider=%s payload_keys=%s',
            state_data.provider_type,
            ['code', 'client_id', 'client_secret', 'redirect_uri', 'grant_type'],
        )
        token_payload = provider.exchange_code(code=code, redirect_uri=redirect_uri)
        logger.info(
            'OAuth token exchange successful: provider=%s has_access_token=%s has_refresh_token=%s expires_in=%s',
            state_data.provider_type,
            bool(token_payload.get('access_token')),
            bool(token_payload.get('refresh_token')),
            token_payload.get('expires_in', ''),
        )

        access_token = token_payload.get('access_token', '')
        refresh_token = token_payload.get('refresh_token', '')
        expires_in = int(token_payload.get('expires_in', 3600))

        if not access_token:
            raise ValueError('Provider did not return an access token')

        # Fetch canonical identity from the provider using the fresh access token.
        try:
            logger.info('OAuth provider profile fetch starting: provider=%s', state_data.provider_type)
            user_info = provider.fetch_user_info(access_token)
        except Exception as exc:
            logger.exception('OAuth provider profile fetch failed: provider=%s', state_data.provider_type)
            raise ValueError(f'Failed to fetch user identity from provider: {exc}') from exc

        email_address = user_info.get('email', '')
        if not email_address:
            logger.error('OAuth provider returned empty email: provider=%s', state_data.provider_type)
            raise ValueError('Provider did not return an email address — ensure email scope is granted')
        logger.info(
            'OAuth provider profile fetch successful: provider=%s email=%s',
            state_data.provider_type,
            email_address,
        )

        display_name = user_info.get('name', '') or email_address
        from_name = display_name

        account, _ = EmailSendingAccount.objects.update_or_create(
            tenant_id=uuid.UUID(state_data.tenant_id),
            user_id=uuid.UUID(state_data.user_id),
            provider_type=state_data.provider_type,
            email_address=email_address,
            defaults={
                'display_name': display_name,
                'from_name': from_name,
                'status': EmailAccountStatus.CONNECTED,
                'can_send': True,
                'can_receive': False,
                'access_token_encrypted': encrypt_json({'access_token': access_token}),
                'refresh_token_encrypted': encrypt_json({'refresh_token': refresh_token}),
                'token_expires_at': timezone.now() + timedelta(seconds=expires_in),
                'health_status': EmailHealthStatus.HEALTHY,
                'last_success_at': timezone.now(),
                'failure_reason': '',
                'deleted_at': None,  # Restore if previously disconnected
            },
        )

        logger.info(
            'OAuth account DB write successful: account_id=%s provider=%s tenant_id=%s user_id=%s email=%s',
            account.id,
            state_data.provider_type,
            state_data.tenant_id,
            state_data.user_id,
            email_address,
        )

        # Validate provider connection immediately and reflect true operational status.
        connection_ok = provider.validate_connection(account)
        if connection_ok:
            account.status = EmailAccountStatus.CONNECTED
            account.can_send = True
            account.health_status = EmailHealthStatus.HEALTHY
            account.failure_reason = ''
            account.last_success_at = timezone.now()
            account.save(update_fields=['status', 'can_send', 'health_status', 'failure_reason', 'last_success_at', 'updated_at'])
            logger.info('OAuth post-connect validation passed: account_id=%s', account.id)
        else:
            account.status = EmailAccountStatus.ERROR
            account.can_send = False
            account.health_status = EmailHealthStatus.DEGRADED
            account.failure_reason = 'Post-connect validation failed'
            account.save(update_fields=['status', 'can_send', 'health_status', 'failure_reason', 'updated_at'])
            logger.error('OAuth post-connect validation failed: account_id=%s', account.id)

        return account

    @staticmethod
    def test_connection(*, account: EmailSendingAccount) -> tuple[bool, str]:
        provider = get_provider(account.provider_type)
        ok = provider.validate_connection(account)
        account.last_tested_at = timezone.now()
        if ok:
            account.status = EmailAccountStatus.CONNECTED
            account.health_status = EmailHealthStatus.HEALTHY
            account.last_success_at = timezone.now()
            account.failure_reason = ''
            account.save(update_fields=['last_tested_at', 'status', 'health_status', 'last_success_at', 'failure_reason', 'updated_at'])
            return True, ''

        # Attempt refresh when OAuth token is stale.
        if account.provider_type in (EmailProviderType.GMAIL_OAUTH, EmailProviderType.MICROSOFT_OAUTH):
            refreshed = provider.refresh_credentials(account)
            if refreshed:
                return True, ''

        account.status = EmailAccountStatus.ERROR
        account.health_status = EmailHealthStatus.DEGRADED
        account.last_failure_at = timezone.now()
        account.failure_reason = 'Connection validation failed'
        account.save(update_fields=['last_tested_at', 'status', 'health_status', 'last_failure_at', 'failure_reason', 'updated_at'])
        return False, account.failure_reason

    @staticmethod
    def disconnect_account(*, account: EmailSendingAccount):
        account.status = EmailAccountStatus.DISCONNECTED
        account.health_status = EmailHealthStatus.UNKNOWN
        account.deleted_at = timezone.now()
        account.save(update_fields=['status', 'health_status', 'deleted_at', 'updated_at'])

    @staticmethod
    def can_send_from_shared_account(*, tenant_id: str, user_id: str, account_id: str) -> bool:
        return EmailAccountPermission.objects.filter(
            tenant_id=tenant_id,
            email_account_id=account_id,
            user_id=user_id,
            can_send=True,
        ).exists()
