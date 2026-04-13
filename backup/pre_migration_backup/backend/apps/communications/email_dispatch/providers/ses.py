"""
Amazon SES Automation Email Provider
=======================================
Future-ready stub for Amazon Simple Email Service.

Credential fields expected in TenantEmailConfig:
- ses_region            e.g. 'us-east-1'
- ses_access_key_id     AWS access key (plain)
- ses_secret_access_key_encrypted  (encrypted via utils.encrypt_string)

When boto3 is installed, this provider becomes fully functional.
Until then, calling send() raises a clear configuration error logged
to the admin rather than silently failing.

To activate:
    pip install boto3
    Set TenantEmailConfig.provider = 'ses'
    Fill in ses_region, ses_access_key_id, ses_secret_access_key_encrypted
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from apps.communications.email_dispatch.providers.base import (
    AutomationEmailProvider,
    AutomationSendResult,
    ProviderHealthStatus,
)

logger = logging.getLogger(__name__)


class SESProvider(AutomationEmailProvider):
    """Amazon SES provider (requires boto3)."""

    key = 'ses'

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

        try:
            import boto3
        except ImportError:
            error = 'boto3 is not installed. Run: pip install boto3'
            logger.error('SESProvider: %s', error)
            return AutomationSendResult(ok=False, status='failed', error=error)

        region, access_key, secret_key = self._resolve_credentials()
        if not region or not access_key or not secret_key:
            return AutomationSendResult(ok=False, status='failed', error='SES credentials incomplete')

        try:
            client = boto3.client(
                'ses',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
            sender = self._from_header(from_email, from_name)
            body: dict = {}
            if text_body:
                body['Text'] = {'Data': text_body, 'Charset': 'UTF-8'}
            if html_body:
                body['Html'] = {'Data': html_body, 'Charset': 'UTF-8'}
            if not body:
                body['Text'] = {'Data': subject, 'Charset': 'UTF-8'}

            kwargs: dict = {
                'Source': sender,
                'Destination': {'ToAddresses': recipients},
                'Message': {
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': body,
                },
            }
            if reply_to:
                kwargs['ReplyToAddresses'] = [reply_to]

            response = client.send_email(**kwargs)
            msg_id = response.get('MessageId', '')
            logger.debug('SES send OK, MessageId=%s', msg_id)
            return AutomationSendResult(ok=True, status='sent', provider_message_id=msg_id)
        except Exception as exc:
            logger.exception('SESProvider send failure')
            return AutomationSendResult(ok=False, status='failed', error=str(exc))

    def validate_config(self) -> tuple[bool, str]:
        try:
            import boto3  # noqa: F401
        except ImportError:
            return False, 'boto3 is not installed'
        if self.config is None:
            return False, 'TenantEmailConfig required for SES provider'
        region, access_key, _ = self._resolve_credentials()
        if not region:
            return False, 'ses_region is required'
        if not access_key:
            return False, 'ses_access_key_id is required'
        if not self.config.ses_secret_access_key_encrypted:
            return False, 'ses_secret_access_key_encrypted is required'
        if not self.config.from_email:
            return False, 'from_email is required'
        return True, ''

    def health_check(self) -> dict:
        try:
            import boto3
        except ImportError:
            return {
                'status': ProviderHealthStatus.UNHEALTHY,
                'provider': self.key,
                'detail': 'boto3 not installed',
                'latency_ms': None,
            }
        region, access_key, secret_key = self._resolve_credentials()
        if not (region and access_key and secret_key):
            return {
                'status': ProviderHealthStatus.UNHEALTHY,
                'provider': self.key,
                'detail': 'Incomplete SES credentials',
                'latency_ms': None,
            }
        start = time.monotonic()
        try:
            client = boto3.client(
                'ses',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
            client.get_send_quota()
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                'status': ProviderHealthStatus.HEALTHY,
                'provider': self.key,
                'detail': 'SES get_send_quota OK',
                'latency_ms': latency_ms,
            }
        except Exception as exc:
            return {
                'status': ProviderHealthStatus.UNHEALTHY,
                'provider': self.key,
                'detail': str(exc),
                'latency_ms': None,
            }

    # ------------------------------------------------------------------

    def _resolve_credentials(self) -> tuple[str, str, str]:
        if not self.config:
            return '', '', ''
        region = getattr(self.config, 'ses_region', '') or ''
        access_key = getattr(self.config, 'ses_access_key_id', '') or ''
        encrypted_secret = getattr(self.config, 'ses_secret_access_key_encrypted', '') or ''
        if encrypted_secret:
            from apps.communications.utils import decrypt_string
            secret_key = decrypt_string(encrypted_secret)
        else:
            secret_key = ''
        return region, access_key, secret_key
