"""
Push Notification Provider — Architecture-Ready Placeholder
=============================================================
This placeholder provider handles all push channel types (web_push, FCM, APNs)
until full mobile push infrastructure is implemented.

Architecture design:
  • Provider interface is complete and matches the real FCM/APNs contract
  • CommunicationDelivery records are created and tracked in PENDING state
  • Sending is skipped with 'push_not_implemented' skip_reason
  • All delivery attempts are logged for observability

When ready to implement:
  1. Replace `_send_web_push()` with real pywebpush VAPID send
  2. Replace `_send_fcm()` with real google-auth + FCM v1 API send
  3. Replace `_send_apns()` with real httpx2 + APNs JWT send
  4. Remove the `is_placeholder = True` guard in send()

Required config keys (for future use, validated when is_placeholder removed):
    push_provider_type: 'web_push' | 'fcm' | 'apns'

    For web_push:
        push_vapid_public_key
        push_vapid_private_key  (decrypted)
        sender_identifier       (VAPID contact email)

    For fcm:
        api_token               (FCM server key or OAuth2 access token)
        push_fcm_project_id

    For apns:
        api_token               (APNs auth key content, decrypted)
        api_key_id              (APNs key ID)
        push_apns_team_id
        push_apns_bundle_id
"""
import logging
import uuid

from apps.communications.providers.base import (
    BaseChannelProvider,
    SendResult,
    HealthCheckResult,
)

logger = logging.getLogger(__name__)

# Set to False when real push implementation is ready
IS_PLACEHOLDER = True


class PlaceholderPushProvider(BaseChannelProvider):
    """
    Placeholder push provider.

    All sends are logged and tracked as SKIPPED with a clear reason.
    The delivery record is still created so the system can report
    'push delivery pending implementation'.
    """

    PROVIDER_NAME = 'placeholder'
    CHANNEL_TYPE  = 'push'

    def validate_config(self) -> None:
        # Placeholder: no config required
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
        if IS_PLACEHOLDER:
            msg_id = f'push_placeholder_{uuid.uuid4().hex[:12]}'
            logger.debug(
                '[PushPlaceholder] Push not yet implemented. '
                'Would send to %s: subject=%r, body_preview=%r',
                self._safe_log_recipient(recipient),
                subject,
                body[:60] if body else '',
            )
            # Return as success=False with a non-error skip indicator
            # channel_services.py will mark the delivery as SKIPPED
            return SendResult(
                success=False,
                external_message_id=msg_id,
                raw_response={'reason': 'push_not_implemented', 'placeholder': True},
                error='push_not_implemented',
            )

        # Future real implementation will branch here:
        push_type = self.config.get('push_provider_type', 'web_push')
        if push_type == 'fcm':
            return _send_fcm(self.config, recipient, subject, body, metadata or {})
        elif push_type == 'apns':
            return _send_apns(self.config, recipient, subject, body, metadata or {})
        else:
            return _send_web_push(self.config, recipient, subject, body, metadata or {})

    def health_check(self) -> HealthCheckResult:
        if IS_PLACEHOLDER:
            return HealthCheckResult(
                healthy=False,
                latency_ms=0,
                detail='Push provider is placeholder — not yet implemented',
            )
        return HealthCheckResult(healthy=True, detail='Push provider ready')


# ---------------------------------------------------------------------------
# Future implementation stubs
# ---------------------------------------------------------------------------

def _send_web_push(config: dict, recipient: str, title: str, body: str, meta: dict) -> SendResult:
    """Stub: replace with pywebpush VAPID implementation."""
    raise NotImplementedError('Web Push not yet implemented')


def _send_fcm(config: dict, recipient: str, title: str, body: str, meta: dict) -> SendResult:
    """Stub: replace with Firebase Admin SDK or FCM v1 HTTP implementation."""
    raise NotImplementedError('FCM not yet implemented')


def _send_apns(config: dict, recipient: str, title: str, body: str, meta: dict) -> SendResult:
    """Stub: replace with APNs HTTP/2 JWT implementation."""
    raise NotImplementedError('APNs not yet implemented')
