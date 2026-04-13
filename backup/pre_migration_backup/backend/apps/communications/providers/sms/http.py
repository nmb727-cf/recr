"""
Generic HTTP SMS Provider
==========================
Sends SMS via any HTTP-based gateway that accepts a simple POST request.

This provider is intentionally generic — configure it to match your
SMS gateway's API by providing the right endpoint, method, and body template.

Required config keys:
    sms_http_endpoint  — full URL of the SMS API endpoint
    api_token          — API key / bearer token

Optional config keys:
    sms_http_method          — 'POST' (default) or 'GET'
    sender_identifier        — sender name or number
    body_template            — JSON template string with {to}, {body}, {from} placeholders
    auth_header_name         — header name for auth token (default: 'Authorization')
    auth_header_prefix       — prefix before token (default: 'Bearer ')
    response_id_field        — JSON field containing the message ID (default: 'id')
    extra_headers            — dict of additional headers (from config_json)

Body template example (config['body_template']):
    '{{"to": "{to}", "message": "{body}", "sender": "{from}"}}'

If body_template is not set, the provider sends:
    {"to": "<phone>", "message": "<body>", "sender": "<sender_identifier>"}
"""
import json
import logging
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


class GenericHTTPSMSProvider(BaseChannelProvider):

    PROVIDER_NAME = 'generic_http'
    CHANNEL_TYPE  = 'sms'

    def validate_config(self) -> None:
        self._require_config('sms_http_endpoint', 'api_token')

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
        endpoint       = self.config['sms_http_endpoint']
        token          = self.config['api_token']
        method         = self.config.get('sms_http_method', 'POST').upper()
        sender         = self.config.get('sender_identifier', '')
        auth_header    = self.config.get('auth_header_name', 'Authorization')
        auth_prefix    = self.config.get('auth_header_prefix', 'Bearer ')
        id_field       = self.config.get('response_id_field', 'id')
        body_template  = self.config.get('body_template', '')
        extra_headers  = self.config.get('extra_headers', {})
        recipient      = _normalise_phone(recipient)

        if body_template:
            try:
                payload_str = body_template.format(
                    to=recipient, body=body, **{'from': sender}
                )
                payload = json.loads(payload_str)
            except Exception as exc:
                logger.warning('GenericHTTP: body_template format failed: %s', exc)
                payload = {'to': recipient, 'message': body, 'sender': sender}
        else:
            payload = {'to': recipient, 'message': body, 'sender': sender}

        headers = {
            auth_header: f'{auth_prefix}{token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            **extra_headers,
        }
        encoded_payload = json.dumps(payload).encode()
        req = urllib.request.Request(
            endpoint,
            data=encoded_payload if method in ('POST', 'PUT', 'PATCH') else None,
            headers=headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = {}
                try:
                    resp_data = json.loads(resp.read().decode())
                except Exception:
                    pass
                msg_id = str(resp_data.get(id_field, ''))
                logger.info(
                    'GenericHTTP SMS: sent to %s, msg_id=%s',
                    self._safe_log_recipient(recipient), msg_id,
                )
                return SendResult(
                    success=True,
                    external_message_id=msg_id,
                    raw_response={id_field: msg_id},
                )
        except urllib.error.HTTPError as exc:
            msg = f'HTTP {exc.code}'
            try:
                err = json.loads(exc.read().decode())
                msg = err.get('message') or err.get('error') or msg
            except Exception:
                pass
            logger.warning(
                'GenericHTTP SMS error %s for %s: %s',
                exc.code, self._safe_log_recipient(recipient), msg,
            )
            if exc.code >= 500:
                raise ProviderUnavailableError(f'SMS gateway server error {exc.code}')
            raise ProviderSendError(msg, retryable=(exc.code == 429))
        except urllib.error.URLError as exc:
            raise ProviderUnavailableError(f'SMS gateway unreachable: {exc.reason}')

    def health_check(self) -> HealthCheckResult:
        """
        Generic HTTP gateways usually don't have a standard health endpoint.
        We do a HEAD request to the endpoint and consider 2xx/4xx as 'reachable'.
        """
        import time
        endpoint = self.config['sms_http_endpoint']
        req = urllib.request.Request(endpoint, method='HEAD')
        start = time.monotonic()
        try:
            urllib.request.urlopen(req, timeout=5)
            latency = (time.monotonic() - start) * 1000
            return HealthCheckResult(
                healthy=True,
                latency_ms=round(latency, 1),
                detail='Gateway reachable',
            )
        except urllib.error.HTTPError as exc:
            # 4xx from the gateway means it's reachable but auth/method rejected
            latency = (time.monotonic() - start) * 1000
            return HealthCheckResult(
                healthy=exc.code < 500,
                latency_ms=round(latency, 1),
                detail=f'HTTP {exc.code}',
            )
        except Exception as exc:
            return HealthCheckResult(healthy=False, detail=str(exc))


def _normalise_phone(phone: str) -> str:
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    if cleaned and not cleaned.startswith('+'):
        cleaned = f'+{cleaned}'
    return cleaned
