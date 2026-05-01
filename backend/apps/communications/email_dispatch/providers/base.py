"""
Automation Email Provider — Base Interface
==========================================
Abstract base class for all automation email providers.

Each provider must implement:
- send()        — dispatch a single email message
- validate_config() — verify the config is complete and correct
- health_check()    — return live connectivity status

Providers are stateless — they receive a TenantEmailConfig (or None for
system defaults) at construction time and expose no state between calls.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


class ProviderHealthStatus:
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'
    UNKNOWN = 'unknown'


@dataclass
class AutomationSendResult:
    """Normalized result returned by every provider.send() call."""
    ok: bool
    provider_message_id: str = ''
    status: str = 'sent'          # sent | failed
    error: str = ''
    raw: dict = field(default_factory=dict)


class AutomationEmailProvider(ABC):
    """
    Abstract base for automation email providers.

    Providers are used ONLY by EmailDeliveryService.
    They must never be called directly from business or UI modules.
    """

    #: Short identifier used to tag EmailDelivery.provider
    key: str = 'base'

    def __init__(self, config):
        """
        Args:
            config: TenantEmailConfig instance, or None to use system defaults.
        """
        self.config = config

    # ------------------------------------------------------------------
    # Abstract interface — every provider must implement these
    # ------------------------------------------------------------------

    @abstractmethod
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
        """
        Dispatch a single email.

        Args:
            from_email:  Sender address (e.g. "no-reply@company.com")
            from_name:   Display name (e.g. "Talentos ATS")
            to:          List of recipient email addresses
            subject:     Email subject line
            html_body:   HTML body (may be empty string)
            text_body:   Plain-text body (required fallback)
            reply_to:    Optional reply-to address
            metadata:    Extra data for logging / tracing

        Returns:
            AutomationSendResult with ok=True on success
        """

    @abstractmethod
    def validate_config(self) -> tuple[bool, str]:
        """
        Verify that the provider configuration is complete and valid.

        Returns:
            (is_valid: bool, error_message: str)
            error_message is empty string on success.
        """

    @abstractmethod
    def health_check(self) -> dict:
        """
        Perform a live connectivity check.

        Returns:
            {
                'status': 'healthy' | 'degraded' | 'unhealthy' | 'unknown',
                'provider': self.key,
                'detail': str,
                'latency_ms': int | None,
            }
        """

    # ------------------------------------------------------------------
    # Helpers available to all providers
    # ------------------------------------------------------------------

    def _from_header(self, from_email: str, from_name: str) -> str:
        """Format 'Display Name <email@example.com>' or just the address."""
        if from_name:
            return f'{from_name} <{from_email}>'
        return from_email

    def _safe_recipients(self, to: list[str]) -> list[str]:
        """Strip whitespace and filter out empty strings."""
        return [addr.strip() for addr in (to or []) if addr and addr.strip()]
