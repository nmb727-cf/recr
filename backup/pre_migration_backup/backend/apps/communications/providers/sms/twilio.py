"""
Twilio SMS Provider
====================
Sends SMS via Twilio Messaging API.

Required config keys:
    api_key_id         — Twilio Account SID
    api_token          — Twilio Auth Token
    sender_identifier  — From number (E.164) or Messaging Service SID

Reference: https://www.twilio.com/docs/sms/api
"""
import base64
import json
import logging
import urllib.parse
import urllib.request
import urllib.error

from apps.communications.providers.base import (
    BaseChannelProvider,
    SendResult,
    HealthCheckResult,
    ProviderSendError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)

_TWILIO_BASE = 'https://api.twilio.com/2010-04-01'


class TwilioSMSProvider(BaseChannelProvider):

    PROVIDER_NAME = 'twilio'
    CHANNEL_TYPE  = 'sms'

    def validate_config(self) -> None:
        self._require_config('api_key_id', 'api_token', 'sender_identifier')

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
        account_sid = self.config['api_key_id']
        auth_token  = self.config['api_token']
        from_number = self.config['sender_identifier']
        url = f'{_TWILIO_BASE}/Accounts/{account_sid}/Messages.json'

        form_data = {
            'To':   _normalise_phone(recipient),
            'From': from_number,
            'Body': body[:1600],  # SMS 1600-char limit
        }
        payload     = urllib.parse.urlencode(form_data).encode()
        credentials = base64.b64encode(f'{account_sid}:{auth_token}'.encode()).decode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            method='POST',
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                sid  = data.get('sid', '')
                logger.info(
                    'Twilio SMS: sent to %s, sid=%s',
                    self._safe_log_recipient(recipient), sid,
                )
                return SendResult(
                    success=True,
                    external_message_id=sid,
                    raw_response={'sid': sid, 'status': data.get('status', '')},
                )
        except urllib.error.HTTPError as exc:
            try:
                err = json.loads(exc.read().decode())
            except Exception:
                err = {}
            msg = err.get('message', str(exc))
            logger.warning(
                'Twilio SMS HTTP error %s for %s: %s',
                exc.code, self._safe_log_recipient(recipient), msg,
            )
            if exc.code >= 500:
                raise ProviderUnavailableError(f'Twilio server error {exc.code}')
            raise ProviderSendError(msg, retryable=(exc.code == 429))
        except urllib.error.URLError as exc:
            raise ProviderUnavailableError(f'Twilio unreachable: {exc.reason}')

    def health_check(self) -> HealthCheckResult:
        import time
        account_sid = self.config['api_key_id']
        auth_token  = self.config['api_token']
        url         = f'{_TWILIO_BASE}/Accounts/{account_sid}.json'
        credentials = base64.b64encode(f'{account_sid}:{auth_token}'.encode()).decode()
        req         = urllib.request.Request(
            url, headers={'Authorization': f'Basic {credentials}'}
        )
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=5):
                return HealthCheckResult(
                    healthy=True,
                    latency_ms=round((time.monotonic() - start) * 1000, 1),
                    detail='Twilio SMS credentials verified',
                )
        except Exception as exc:
            return HealthCheckResult(healthy=False, detail=str(exc))


def _normalise_phone(phone: str) -> str:
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    if cleaned and not cleaned.startswith('+'):
        cleaned = f'+{cleaned}'
    return cleaned
