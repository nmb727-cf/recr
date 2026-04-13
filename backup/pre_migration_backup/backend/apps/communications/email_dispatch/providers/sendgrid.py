"""
SendGrid Automation Email Provider
=====================================
Sends transactional email via the SendGrid Web API v3.

Credentials are read from TenantEmailConfig.sendgrid_api_key_encrypted.

This provider uses urllib (stdlib) for the HTTP call so it has zero
additional runtime dependencies.  If the `sendgrid` PyPI package is
installed it is used instead for richer error handling.

Design notes:
- API key is decrypted on every send call (no in-memory caching)
- health_check() sends a dry-run API credentials validation request
- provider_message_id maps to the X-Message-Id response header
"""
from __future__ import annotations

import json
import logging
import time
import urllib.request
import urllib.error
from typing import Optional

from apps.communications.email_dispatch.providers.base import (
    AutomationEmailProvider,
    AutomationSendResult,
    ProviderHealthStatus,
)

logger = logging.getLogger(__name__)

SENDGRID_SEND_URL = 'https://api.sendgrid.com/v3/mail/send'
SENDGRID_VALIDATE_URL = 'https://api.sendgrid.com/v3/scopes'


class SendGridProvider(AutomationEmailProvider):
    """SendGrid API v3 provider for automation/notification emails."""

    key = 'sendgrid'

    def send(
        self,
        *,
        from_email: str,
        from_name: str,
        to: list[str],
        subject: str,
        html_body: str,
        text_body: str,
        reply_to: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AutomationSendResult:
        recipients = self._safe_recipients(to)
        if not recipients:
            return AutomationSendResult(ok=False, status='failed', error='No valid recipients')

        api_key = self._resolve_api_key()
        if not api_key:
            return AutomationSendResult(ok=False, status='failed', error='SendGrid API key not configured')

        payload = self._build_payload(
            from_email=from_email,
            from_name=from_name,
            recipients=recipients,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            reply_to=reply_to,
        )

        # Try the sendgrid SDK first (richer error info), fall back to urllib
        try:
            import sendgrid as sg_sdk
            return self._send_via_sdk(api_key, payload)
        except ImportError:
            return self._send_via_urllib(api_key, payload)

    def validate_config(self) -> tuple[bool, str]:
        if self.config is None:
            return False, 'TenantEmailConfig required for SendGrid provider'
        api_key = self._resolve_api_key()
        if not api_key:
            return False, 'sendgrid_api_key_encrypted is missing or decrypts to empty'
        if not self.config.from_email:
            return False, 'from_email is required'
        return True, ''

    def health_check(self) -> dict:
        api_key = self._resolve_api_key()
        if not api_key:
            return {
                'status': ProviderHealthStatus.UNHEALTHY,
                'provider': self.key,
                'detail': 'API key not configured',
                'latency_ms': None,
            }
        start = time.monotonic()
        try:
            req = urllib.request.Request(
                SENDGRID_VALIDATE_URL,
                headers={'Authorization': f'Bearer {api_key}'},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                latency_ms = int((time.monotonic() - start) * 1000)
                if resp.status == 200:
                    return {
                        'status': ProviderHealthStatus.HEALTHY,
                        'provider': self.key,
                        'detail': 'SendGrid API key valid',
                        'latency_ms': latency_ms,
                    }
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                return {
                    'status': ProviderHealthStatus.DEGRADED,
                    'provider': self.key,
                    'detail': 'API key lacks send scope but is authenticated',
                    'latency_ms': None,
                }
            return {
                'status': ProviderHealthStatus.UNHEALTHY,
                'provider': self.key,
                'detail': f'HTTP {exc.code}: {exc.reason}',
                'latency_ms': None,
            }
        except Exception as exc:
            return {
                'status': ProviderHealthStatus.UNHEALTHY,
                'provider': self.key,
                'detail': str(exc),
                'latency_ms': None,
            }
        return {
            'status': ProviderHealthStatus.UNKNOWN,
            'provider': self.key,
            'detail': 'Unexpected response',
            'latency_ms': None,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_api_key(self) -> str:
        if not self.config or not self.config.sendgrid_api_key_encrypted:
            return ''
        from apps.communications.utils import decrypt_string
        return decrypt_string(self.config.sendgrid_api_key_encrypted)

    def _build_payload(self, *, from_email, from_name, recipients, subject, html_body, text_body, reply_to) -> dict:
        payload: dict = {
            'personalizations': [{'to': [{'email': addr} for addr in recipients]}],
            'from': {'email': from_email, 'name': from_name or ''},
            'subject': subject,
            'content': [],
        }
        if text_body:
            payload['content'].append({'type': 'text/plain', 'value': text_body})
        if html_body:
            payload['content'].append({'type': 'text/html', 'value': html_body})
        if not payload['content']:
            payload['content'].append({'type': 'text/plain', 'value': subject})
        if reply_to:
            payload['reply_to'] = {'email': reply_to}
        return payload

    def _send_via_urllib(self, api_key: str, payload: dict) -> AutomationSendResult:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            SENDGRID_SEND_URL,
            data=body,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                msg_id = resp.headers.get('X-Message-Id', '')
                logger.debug('SendGrid send OK, message_id=%s', msg_id)
                return AutomationSendResult(ok=True, status='sent', provider_message_id=msg_id)
        except urllib.error.HTTPError as exc:
            raw_body = ''
            try:
                raw_body = exc.read().decode()
            except Exception:
                pass
            error = f'SendGrid HTTP {exc.code}: {raw_body[:500]}'
            logger.error('SendGridProvider HTTP error: %s', error)
            return AutomationSendResult(ok=False, status='failed', error=error, raw={'status_code': exc.code, 'body': raw_body})
        except Exception as exc:
            logger.exception('SendGridProvider unexpected failure')
            return AutomationSendResult(ok=False, status='failed', error=str(exc))

    def _send_via_sdk(self, api_key: str, payload: dict) -> AutomationSendResult:
        """Use the sendgrid Python SDK when installed."""
        import sendgrid as sg_sdk
        from sendgrid.helpers.mail import Mail, Email, To, Content

        client = sg_sdk.SendGridAPIClient(api_key=api_key)
        try:
            response = client.client.mail.send.post(request_body=payload)
            msg_id = response.headers.get('X-Message-Id', '') if hasattr(response, 'headers') else ''
            if response.status_code in (200, 202):
                return AutomationSendResult(ok=True, status='sent', provider_message_id=str(msg_id))
            error = f'SendGrid SDK status {response.status_code}: {response.body}'
            return AutomationSendResult(ok=False, status='failed', error=error)
        except Exception as exc:
            logger.exception('SendGrid SDK send failure')
            return AutomationSendResult(ok=False, status='failed', error=str(exc))
