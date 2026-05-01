"""
BaseChannelProvider — Abstract interface all channel providers must implement.

Every provider receives a config dict at construction (sourced from
TenantChannelConfig.config_json + individual encrypted fields) and exposes
three canonical methods:
  • send(...)         — deliver a message, return SendResult
  • validate_config() — raise ProviderConfigError if required fields missing
  • health_check()    — lightweight connectivity probe, return HealthCheckResult

All providers must be:
  • Stateless (safe to instantiate per-request or per-task)
  • Exception-safe (wrap external calls; never bubble raw HTTP errors)
  • Log-safe (never log raw credentials or PII beyond the last 4 chars)
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class SendResult:
    """
    Canonical result returned by provider.send().

    success:             True if the message was accepted by the provider.
    external_message_id: Provider-issued message ID for delivery tracking.
    raw_response:        Sanitised provider response payload (no credentials).
    error:               Human-readable error if success=False.
    """
    success:             bool
    external_message_id: str = ''
    raw_response:        dict = field(default_factory=dict)
    error:               str = ''


@dataclass
class HealthCheckResult:
    """
    Canonical result returned by provider.health_check().

    healthy: True if the provider API is reachable and credentials are valid.
    latency_ms: Round-trip latency in milliseconds (0 if not measured).
    detail: Human-readable status message.
    """
    healthy:    bool
    latency_ms: float = 0.0
    detail:     str   = ''


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ProviderError(Exception):
    """Base class for all provider errors."""


class ProviderConfigError(ProviderError):
    """Required configuration field is missing or invalid."""


class ProviderUnavailableError(ProviderError):
    """Provider API is unreachable or returned a 5xx response."""


class ProviderSendError(ProviderError):
    """
    Provider accepted the request but returned a logical send failure
    (e.g. invalid phone number, template not approved, rate-limited).
    """
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


# ---------------------------------------------------------------------------
# BaseChannelProvider
# ---------------------------------------------------------------------------

class BaseChannelProvider(ABC):
    """
    Abstract base class for all channel providers.

    Subclasses implement send(), validate_config(), and health_check().
    The __init__ signature is fixed: always (self, config: dict).
    """

    # Provider identifier — set on concrete subclasses
    PROVIDER_NAME:  str = 'base'
    CHANNEL_TYPE:   str = 'unknown'

    def __init__(self, config: dict):
        """
        Args:
            config: dict sourced from TenantChannelConfig (already decrypted).
                    Concrete providers document which keys they require.
        """
        self.config = config or {}
        self.validate_config()

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def send(
        self,
        *,
        recipient: str,
        body: str,
        subject: str = '',
        template_name: str = '',
        template_params: dict = None,
        metadata: dict = None,
    ) -> SendResult:
        """
        Deliver a message to the recipient.

        Args:
            recipient:       Normalised identifier (E.164 phone, push token, etc.)
            body:            Rendered message body (plain text / pre-rendered)
            subject:         Optional subject / title (push only)
            template_name:   Provider template ID or slug (WhatsApp requires this)
            template_params: Variable values for provider-side template substitution
            metadata:        Pass-through metadata (tenant_id, notification_id, etc.)

        Returns:
            SendResult

        Raises:
            ProviderSendError  — logical failure (bad number, unapproved template)
            ProviderUnavailableError — network / 5xx failure
        """

    @abstractmethod
    def validate_config(self) -> None:
        """
        Raise ProviderConfigError if required config keys are missing.
        Called automatically at __init__ time.
        """

    @abstractmethod
    def health_check(self) -> HealthCheckResult:
        """
        Probe the provider API with a lightweight request.
        Must NOT send real messages.

        Returns:
            HealthCheckResult
        """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _require_config(self, *keys: str) -> None:
        """Assert that all listed keys are present and non-empty in self.config."""
        missing = [k for k in keys if not self.config.get(k)]
        if missing:
            raise ProviderConfigError(
                f'{self.__class__.__name__}: missing required config key(s): {missing}'
            )

    def _safe_log_recipient(self, recipient: str) -> str:
        """Return a redacted version of the recipient for safe logging."""
        if not recipient:
            return '(empty)'
        if len(recipient) <= 4:
            return '****'
        return f'{recipient[:3]}***{recipient[-2:]}'
