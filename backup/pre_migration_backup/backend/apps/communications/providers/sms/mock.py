"""Mock SMS Provider — Development / Test Use Only"""
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


class MockSMSProvider(BaseChannelProvider):

    PROVIDER_NAME = 'mock'
    CHANNEL_TYPE  = 'sms'

    sent_messages: list = []

    def validate_config(self) -> None:
        pass

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
            raise ProviderUnavailableError('Mock SMS: simulated outage')
        if self.config.get('fail'):
            raise ProviderSendError('Mock SMS: simulated failure', retryable=False)

        msg_id = f'mock_sms_{uuid.uuid4().hex[:12]}'
        record = {
            'message_id': msg_id,
            'recipient':  recipient,
            'body':       body,
            'metadata':   metadata or {},
        }
        MockSMSProvider.sent_messages.append(record)
        logger.debug('[MockSMS] Sent to %s | msg_id=%s', self._safe_log_recipient(recipient), msg_id)
        return SendResult(success=True, external_message_id=msg_id, raw_response=record)

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(healthy=True, latency_ms=0.1, detail='Mock: always healthy')

    @classmethod
    def clear(cls):
        cls.sent_messages.clear()
