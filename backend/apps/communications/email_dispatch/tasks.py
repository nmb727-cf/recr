from datetime import datetime

from celery import shared_task
from django.utils import timezone

from apps.communications.email_dispatch.dispatch import EmailDispatchService
from apps.communications.email_dispatch.types import EmailSendRequest


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, payload: dict):
    schedule_at = payload.pop('schedule_at', None)
    if schedule_at:
        parsed_schedule = datetime.fromisoformat(schedule_at)
        if parsed_schedule.tzinfo is None:
            parsed_schedule = timezone.make_aware(parsed_schedule)
        if parsed_schedule > timezone.now():
            raise self.retry(countdown=int((parsed_schedule - timezone.now()).total_seconds()))

    request = EmailSendRequest(**payload)
    message = EmailDispatchService.send_now(request)
    return str(message.id)
