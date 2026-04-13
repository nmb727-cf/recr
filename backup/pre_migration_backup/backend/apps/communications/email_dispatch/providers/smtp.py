"""
SMTP Automation Email Provider
================================
Sends emails via SMTP using credentials from TenantEmailConfig.
Falls back to Django EMAIL_* settings when config is None (system default).

This provider handles:
- TLS / SSL connections
- Plain-text + HTML multipart messages
- Connection-level error capture with structured logging
"""
from __future__ import annotations

import logging
import smtplib
import time
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

from apps.communications.email_dispatch.providers.base import (
    AutomationEmailProvider,
    AutomationSendResult,
    ProviderHealthStatus,
)

logger = logging.getLogger(__name__)


class SMTPAutomationProvider(AutomationEmailProvider):
    """SMTP provider for automation/notification emails."""

    key = 'smtp'

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
            connection = self._get_connection()
            sender = self._from_header(from_email or self._default_from_email(), from_name)
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body or '',
                from_email=sender,
                to=recipients,
                reply_to=[reply_to] if reply_to else None,
                connection=connection,
            )
            if html_body:
                msg.attach_alternative(html_body, 'text/html')
            msg.send()
            logger.debug(
                'SMTP automation send OK → %s recipients, subject=%r',
                len(recipients), subject[:60],
            )
            return AutomationSendResult(ok=True, status='sent')
        except smtplib.SMTPAuthenticationError as exc:
            error = f'SMTP auth failed: {exc}'
            logger.error('SMTPAutomationProvider auth error: %s', exc)
            return AutomationSendResult(ok=False, status='failed', error=error)
        except smtplib.SMTPException as exc:
            error = f'SMTP error: {exc}'
            logger.error('SMTPAutomationProvider send error: %s', exc)
            return AutomationSendResult(ok=False, status='failed', error=error)
        except Exception as exc:
            error = f'Unexpected error: {exc}'
            logger.exception('SMTPAutomationProvider unexpected failure')
            return AutomationSendResult(ok=False, status='failed', error=error)

    def validate_config(self) -> tuple[bool, str]:
        if self.config is None:
            # System defaults — valid if Django EMAIL_HOST is set
            host = getattr(settings, 'EMAIL_HOST', '')
            if not host:
                return False, 'EMAIL_HOST not configured in settings'
            return True, ''
        # TenantEmailConfig validation
        if not self.config.smtp_host:
            return False, 'smtp_host is required'
        if not self.config.smtp_port:
            return False, 'smtp_port is required'
        if not self.config.from_email:
            return False, 'from_email is required'
        return True, ''

    def health_check(self) -> dict:
        start = time.monotonic()
        try:
            conn = self._get_connection()
            conn.open()
            conn.close()
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                'status': ProviderHealthStatus.HEALTHY,
                'provider': self.key,
                'detail': 'SMTP connection OK',
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
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_connection(self):
        """Build a Django SMTP connection from TenantEmailConfig or system defaults."""
        if self.config is None:
            return get_connection()  # uses Django EMAIL_* settings

        from apps.communications.utils import decrypt_string
        return get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=self.config.smtp_host,
            port=self.config.smtp_port,
            username=self.config.smtp_username or '',
            password=decrypt_string(self.config.smtp_password_encrypted) if self.config.smtp_password_encrypted else '',
            use_tls=self.config.smtp_use_tls,
            use_ssl=self.config.smtp_use_ssl,
        )

    def _default_from_email(self) -> str:
        if self.config and self.config.from_email:
            return self.config.from_email
        return getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@talentos.com')
