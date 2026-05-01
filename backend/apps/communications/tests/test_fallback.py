"""
QA Tests: Fallback Email Scheduling + Escalation Logic
"""
import uuid
from unittest.mock import patch, MagicMock, call, Mock

from django.test import TestCase
from django.utils import timezone

from apps.communications.models import Notification, NotificationDelivery, NotificationSeverity
from apps.communications.notification_service import (
    NotificationService,
    FALLBACK_DELAY_BY_SEVERITY,
)

TENANT_A = uuid.uuid4()
USER_1 = uuid.uuid4()


def _make_notification(severity=NotificationSeverity.HIGH, is_read=False, tenant_id=None):
    return Notification.objects.create(
        user_id=USER_1,
        tenant_id=tenant_id or TENANT_A,
        title='Test',
        body='Body',
        type='test.event',
        notification_type='test.event',
        severity=severity,
        is_read=is_read,
    )


class TestFallbackDelayConfig(TestCase):

    def test_info_has_no_fallback(self):
        self.assertIsNone(FALLBACK_DELAY_BY_SEVERITY[NotificationSeverity.INFO])

    def test_medium_fallback_is_40_min(self):
        delay = FALLBACK_DELAY_BY_SEVERITY[NotificationSeverity.MEDIUM]
        self.assertGreaterEqual(delay, 2400)
        self.assertLessEqual(delay, 3600)

    def test_high_fallback_is_10_min(self):
        delay = FALLBACK_DELAY_BY_SEVERITY[NotificationSeverity.HIGH]
        self.assertLessEqual(delay, 900)

    def test_critical_fallback_is_near_immediate(self):
        delay = FALLBACK_DELAY_BY_SEVERITY[NotificationSeverity.CRITICAL]
        self.assertLessEqual(delay, 120)


class TestScheduleFallbackIfNeeded(TestCase):

    @patch('apps.communications.notification_orchestration_service.schedule_automation_job')
    def test_high_severity_schedules_task(self, mock_schedule):
        mock_schedule.return_value = MagicMock()
        n = _make_notification(severity=NotificationSeverity.HIGH)
        NotificationService._schedule_fallback_if_needed(n)
        mock_schedule.assert_called_once()
        call_kwargs = mock_schedule.call_args.kwargs
        self.assertEqual(call_kwargs['notification_id'], str(n.id))
        self.assertLessEqual(call_kwargs['delay_seconds'], 900)

    @patch('apps.communications.notification_orchestration_service.schedule_automation_job')
    def test_info_severity_does_not_schedule(self, mock_schedule):
        n = _make_notification(severity=NotificationSeverity.INFO)
        NotificationService._schedule_fallback_if_needed(n)
        mock_schedule.assert_not_called()

    @patch('apps.communications.notification_orchestration_service.schedule_automation_job')
    def test_critical_schedules_with_short_countdown(self, mock_schedule):
        mock_schedule.return_value = MagicMock()
        n = _make_notification(severity=NotificationSeverity.CRITICAL)
        NotificationService._schedule_fallback_if_needed(n)
        mock_schedule.assert_called_once()
        call_kwargs = mock_schedule.call_args.kwargs
        self.assertLessEqual(call_kwargs['delay_seconds'], 120)


class TestCheckAndSendFallbackTask(TestCase):

    @patch('apps.communications.fallback_tasks._send_fallback_email')
    def test_skips_if_already_read(self, mock_send):
        n = _make_notification(is_read=True)
        from apps.communications.fallback_tasks import check_and_send_fallback_email
        check_and_send_fallback_email(str(n.id))
        mock_send.assert_not_called()

    @patch('apps.communications.fallback_tasks.escalate_notification.apply_async')
    @patch('apps.communications.fallback_tasks._send_fallback_email')
    def test_skips_if_fallback_already_sent(self, mock_send, mock_escalate):
        n = _make_notification(is_read=False)
        n.fallback_email_sent_at = timezone.now()
        n.save()
        from apps.communications.fallback_tasks import check_and_send_fallback_email
        check_and_send_fallback_email(str(n.id))
        mock_send.assert_not_called()

    @patch('apps.communications.fallback_tasks.escalate_notification.apply_async')
    @patch('apps.communications.fallback_tasks._send_fallback_email')
    def test_sends_email_if_unread(self, mock_send, mock_escalate):
        n = _make_notification(is_read=False, severity=NotificationSeverity.HIGH)
        from apps.communications.fallback_tasks import check_and_send_fallback_email
        check_and_send_fallback_email(str(n.id))
        mock_send.assert_called_once_with(n)
        # Should schedule escalation for HIGH severity
        mock_escalate.assert_called_once()

    @patch('apps.communications.fallback_tasks._send_fallback_email')
    def test_graceful_on_missing_notification(self, mock_send):
        from apps.communications.fallback_tasks import check_and_send_fallback_email
        # Should not raise
        check_and_send_fallback_email(str(uuid.uuid4()))
        mock_send.assert_not_called()


class TestRecordDeliveryUpdatesNotification(TestCase):

    def test_fallback_email_sent_at_updated_on_success(self):
        n = _make_notification()
        NotificationService.record_delivery_attempt(
            notification_id=n.id,
            channel='email',
            provider='system',
            status='sent',
            tenant_id=TENANT_A,
        )
        n.refresh_from_db()
        self.assertIsNotNone(n.fallback_email_sent_at)

    def test_failed_delivery_does_not_update_sent_at(self):
        n = _make_notification()
        NotificationService.record_delivery_attempt(
            notification_id=n.id,
            channel='email',
            provider='system',
            status='failed',
            error_message='SMTP error',
            tenant_id=TENANT_A,
        )
        n.refresh_from_db()
        self.assertIsNone(n.fallback_email_sent_at)

    def test_delivery_record_created(self):
        n = _make_notification()
        delivery = NotificationService.record_delivery_attempt(
            notification_id=n.id,
            channel='email',
            status='sent',
        )
        self.assertEqual(delivery.channel, 'email')
        self.assertEqual(delivery.status, 'sent')
        self.assertIsNotNone(delivery.attempted_at)
