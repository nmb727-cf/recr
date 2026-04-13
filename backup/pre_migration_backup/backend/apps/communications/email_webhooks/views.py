from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.communications.email_webhooks.services import EmailWebhookProcessor
from apps.core.responses import error_response, success_response


class EmailWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, provider):
        expected_secret = getattr(settings, 'COMM_EMAIL_WEBHOOK_SECRET', '')
        supplied_secret = request.headers.get('X-Webhook-Secret', '')

        if expected_secret and supplied_secret != expected_secret:
            return error_response('Invalid webhook signature', status_code=403)

        payload = request.data if isinstance(request.data, dict) else {}
        message = EmailWebhookProcessor.process_event(provider=provider, payload=payload)
        return success_response(
            data={'matched': bool(message), 'email_message_id': str(message.id) if message else None},
            message='Webhook accepted.',
        )
