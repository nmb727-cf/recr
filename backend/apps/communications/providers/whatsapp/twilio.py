"""
Twilio WhatsApp Provider
=========================
Sends WhatsApp messages via Twilio's Messaging API (whatsapp: channel prefix).

Required config keys:
    api_key_id   — Twilio Account SID
    api_token    — Twilio Auth Token
    sender_identifier — Sender number in E.164, e.g. '+14155238886'
                        (must be Twilio's WhatsApp sandbox or approved number)

Template / content messages:
    Twilio supports Content API templates. Pass template_name as the Content SID
    and template_params as variables. For simple sends, just pass body.

Reference: https://www.twilio.com/docs/whatsapp/api
"""
import json
import logging
import urllib.parse
import urllib.request
import urllib.error
import base64

from apps.communications.providers.base import (
    BaseChannelProvider,
    SendResult,
    HealthCheckResult,
    ProviderSendError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)

_TWILIO_API_BASE = 'https://api.twilio.com/2010-04-01'


class TwilioWhatsAppProvider(BaseChannelProvider):

    PROVIDER_NAME = 'twilio_whatsapp'
    CHANNEL_TYPE  = 'whatsapp'

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
        account_sid    = self.config['api_key_id']
        auth_token     = self.config['api_token']
        from_number    = self.config['sender_identifier']
        url = f'{_TWILIO_API_BASE}/Accounts/{account_sid}/Messages.json'

        to_wa   = f'whatsapp:{_normalise_phone(recipient)}'
        from_wa = f'whatsapp:{from_number}'

        form_data = {
            'To':   to_wa,
            'From': from_wa,
            'Body': body,
        }
        if template_name:
            # Twilio Content API: pass ContentSid as template_name
            form_data['ContentSid'] = template_name
            if template_params:
                form_data['ContentVariables'] = json.dumps(
                    {str(i + 1): str(v) for i, v in enumerate(template_params.values())}
                )

        payload = urllib.parse.urlencode(form_data).encode()
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
                msg_sid = data.get('sid', '')
                logger.info(
                    'Twilio WA: sent to %s, sid=%s',
                    self._safe_log_recipient(recipient), msg_sid,
                )
                return SendResult(
                    success=True,
                    external_message_id=msg_sid,
                    raw_response={'sid': msg_sid, 'status': data.get('status', '')},
                )
        except urllib.error.HTTPError as exc:
            try:
                err = json.loads(exc.read().decode())
            except Exception:
                err = {}
            msg = err.get('message', str(exc))
            logger.warning(
                'Twilio WA HTTP error %s for %s: %s',
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
        url = f'{_TWILIO_API_BASE}/Accounts/{account_sid}.json'
        credentials = base64.b64encode(f'{account_sid}:{auth_token}'.encode()).decode()
        req = urllib.request.Request(
            url, headers={'Authorization': f'Basic {credentials}'}
        )
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                latency = (time.monotonic() - start) * 1000
                return HealthCheckResult(
                    healthy=True,
                    latency_ms=round(latency, 1),
                    detail=f'account={data.get("friendly_name", account_sid[:8])}',
                )
        except Exception as exc:
            return HealthCheckResult(healthy=False, detail=str(exc))


def _normalise_phone(phone: str) -> str:
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    if cleaned and not cleaned.startswith('+'):
        cleaned = f'+{cleaned}'
    return cleaned
