"""
WhatsApp Business API Provider
================================
Adapter for Meta's WhatsApp Business Platform (Cloud API v19+).

Required config keys (from TenantChannelConfig):
    api_token              — permanent or system user access token
    whatsapp_phone_number_id  — phone number ID from the Business Platform
    (optional) whatsapp_api_version — defaults to 'v19.0'

Template messages:
    Pass template_name and template_params to send a pre-approved template.
    Free-form text is only allowed within a 24-hour customer service window;
    use template_name for all automated/outbound sends.

Reference: https://developers.facebook.com/docs/whatsapp/cloud-api
"""
import json
import logging
from typing import Optional

from apps.communications.providers.base import (
    BaseChannelProvider,
    SendResult,
    HealthCheckResult,
    ProviderConfigError,
    ProviderSendError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)

# Meta's graph API base
_GRAPH_API_BASE = 'https://graph.facebook.com'


class WhatsAppBusinessAPIProvider(BaseChannelProvider):
    """
    Sends WhatsApp messages via Meta's WhatsApp Business Cloud API.

    Template send flow:
        POST /{version}/{phone_number_id}/messages
        {
          "messaging_product": "whatsapp",
          "to": "<E.164 phone>",
          "type": "template",
          "template": {
            "name": "<template_name>",
            "language": {"code": "en_US"},
            "components": [{"type": "body", "parameters": [...]}]
          }
        }
    """

    PROVIDER_NAME = 'whatsapp_business_api'
    CHANNEL_TYPE  = 'whatsapp'

    def validate_config(self) -> None:
        self._require_config('api_token', 'whatsapp_phone_number_id')

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
        Send a WhatsApp message.

        If template_name is provided: sends a template message (required for
        automated/outbound sends outside customer service windows).

        If template_name is empty: sends a free-form text message (only valid
        within a 24-hour session opened by the recipient).
        """
        import urllib.request
        import urllib.error

        token    = self.config['api_token']
        phone_id = self.config['whatsapp_phone_number_id']
        version  = self.config.get('whatsapp_api_version', 'v19.0')
        url      = f'{_GRAPH_API_BASE}/{version}/{phone_id}/messages'

        recipient = _normalise_phone(recipient)

        if template_name:
            payload = _build_template_payload(recipient, template_name, template_params or {})
        else:
            payload = {
                'messaging_product': 'whatsapp',
                'to': recipient,
                'type': 'text',
                'text': {'body': body},
            }

        req_data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_body = json.loads(resp.read().decode())
                msg_id = (
                    resp_body.get('messages', [{}])[0].get('id', '')
                    if resp_body.get('messages') else ''
                )
                logger.info(
                    'WA Business API: sent to %s, msg_id=%s',
                    self._safe_log_recipient(recipient),
                    msg_id,
                )
                return SendResult(
                    success=True,
                    external_message_id=msg_id,
                    raw_response=_sanitise_response(resp_body),
                )
        except urllib.error.HTTPError as exc:
            error_body = {}
            try:
                error_body = json.loads(exc.read().decode())
            except Exception:
                pass
            error_msg = error_body.get('error', {}).get('message', str(exc))
            error_code = error_body.get('error', {}).get('code', exc.code)
            logger.warning(
                'WA Business API HTTP error %s for %s: %s',
                exc.code, self._safe_log_recipient(recipient), error_msg,
            )
            if exc.code >= 500:
                raise ProviderUnavailableError(f'WA API server error {exc.code}: {error_msg}')
            retryable = error_code in (131056, 130429, 131031)  # rate-limit / queue full
            raise ProviderSendError(error_msg, retryable=retryable)

        except urllib.error.URLError as exc:
            logger.error('WA Business API connection error: %s', exc)
            raise ProviderUnavailableError(f'WA API unreachable: {exc.reason}')

    def health_check(self) -> HealthCheckResult:
        """Verify credentials by querying the phone number profile."""
        import urllib.request
        import urllib.error
        import time

        token    = self.config['api_token']
        phone_id = self.config['whatsapp_phone_number_id']
        version  = self.config.get('whatsapp_api_version', 'v19.0')
        url      = f'{_GRAPH_API_BASE}/{version}/{phone_id}?fields=id,display_phone_number'

        req = urllib.request.Request(
            url,
            headers={'Authorization': f'Bearer {token}'},
        )
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                latency = (time.monotonic() - start) * 1000
                return HealthCheckResult(
                    healthy=True,
                    latency_ms=round(latency, 1),
                    detail=f'phone={data.get("display_phone_number", phone_id)}',
                )
        except Exception as exc:
            return HealthCheckResult(healthy=False, detail=str(exc))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_phone(phone: str) -> str:
    """Strip spaces and dashes; ensure E.164 format (starts with +)."""
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    if cleaned and not cleaned.startswith('+'):
        cleaned = f'+{cleaned}'
    return cleaned


def _build_template_payload(recipient: str, template_name: str, params: dict) -> dict:
    """Build a WhatsApp template message payload."""
    components = []
    if params:
        body_params = [
            {'type': 'text', 'text': str(v)}
            for v in params.values()
            if v is not None
        ]
        if body_params:
            components.append({'type': 'body', 'parameters': body_params})

    return {
        'messaging_product': 'whatsapp',
        'to': recipient,
        'type': 'template',
        'template': {
            'name': template_name,
            'language': {'code': 'en_US'},
            'components': components,
        },
    }


def _sanitise_response(resp: dict) -> dict:
    """Remove any fields that could contain tokens from response before logging."""
    safe = {}
    for k, v in resp.items():
        if k.lower() in ('token', 'access_token', 'secret'):
            safe[k] = '***'
        else:
            safe[k] = v
    return safe
