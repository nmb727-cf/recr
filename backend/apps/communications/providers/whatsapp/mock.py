"""
Mock WhatsApp Provider — Development / Test Use Only
=====================================================
Logs sends to Python logger and optionally to an in-memory send log
(accessible via MockWhatsAppProvider.sent_messages for test assertions).

Set config['fail'] = True to simulate a failure.
Set config['unavailable'] = True to simulate a provider outage.
"""
import logging
import uuid

from apps.communications.providers.base import (
    BaseChannelProvider,
    SendResult,
    HealthCheckResult,
    ProviderSendError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class MockWhatsAppProvider(BaseChannelProvider):

    PROVIDER_NAME = 'mock'
    CHANNEL_TYPE  = 'whatsapp'

    # Class-level send log — cleared between tests with MockWhatsAppProvider.clear()
    sent_messages: list = []

    def validate_config(self) -> None:
        pass  # Mock requires no credentials

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
        if self.config.get('unavailable'):
            raise ProviderUnavailableError('Mock WhatsApp: simulated outage')
        if self.config.get('fail'):
            raise ProviderSendError('Mock WhatsApp: simulated send failure', retryable=False)

        msg_id = f'mock_wa_{uuid.uuid4().hex[:12]}'
        record = {
            'message_id':    msg_id,
            'recipient':     recipient,
            'body':          body,
            'template_name': template_name,
            'template_params': template_params or {},
            'metadata':      metadata or {},
        }
        MockWhatsAppProvider.sent_messages.append(record)
        logger.debug(
            '[MockWA] Sent to %s | template=%r | msg_id=%s',
            self._safe_log_recipient(recipient), template_name, msg_id,
        )
        return SendResult(
            success=True,
            external_message_id=msg_id,
            raw_response=record,
        )

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(healthy=True, latency_ms=0.1, detail='Mock: always healthy')

    @classmethod
    def clear(cls):
        cls.sent_messages.clear()
