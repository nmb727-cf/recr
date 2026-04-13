"""
QA Tests: Event Handlers → Notification Creation
"""
import uuid
from unittest.mock import patch, MagicMock

from django.test import TestCase

from apps.communications.models import Notification, NotificationSeverity
from apps.core import events


def _send_signal(signal, **kwargs):
    """Helper to send Django signal in tests."""
    signal.send(sender=None, **kwargs)


def _mock_app(tenant_id=None):
    app = MagicMock()
    app.id = uuid.uuid4()
    app.tenant_id = tenant_id or uuid.uuid4()
    app.job_title = 'Senior Engineer'
    app.offer_id = uuid.uuid4()
    return app


def _mock_interview(tenant_id=None):
    interview = MagicMock()
    interview.id = uuid.uuid4()
    interview.tenant_id = tenant_id or uuid.uuid4()
    interview.title = 'Technical Round'
    interview.scheduled_at = '2026-04-10 10:00'
    return interview


class TestApplicationEventHandlers(TestCase):
    """Call handlers directly to avoid cross-module signal side effects."""

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_application_submitted_notifies_recruiter(self, mock_rt, mock_fb):
        from apps.communications.event_handlers import on_application_submitted
        recruiter_id = uuid.uuid4()
        app = _mock_app()
        on_application_submitted(sender=None, application=app, recruiter_user_id=recruiter_id)
        n = Notification.objects.filter(
            user_id=recruiter_id,
            notification_type='application.submitted',
        ).first()
        self.assertIsNotNone(n)
        self.assertEqual(n.related_entity_type, 'application')

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_shortlisted_notifies_candidate(self, mock_rt, mock_fb):
        from apps.communications.event_handlers import on_application_shortlisted
        candidate_id = uuid.uuid4()
        app = _mock_app()
        on_application_shortlisted(sender=None, application=app, candidate_user_id=candidate_id)
        n = Notification.objects.filter(
            user_id=candidate_id,
            notification_type='application.shortlisted',
        ).first()
        self.assertIsNotNone(n)
        self.assertEqual(n.severity, NotificationSeverity.MEDIUM)

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_rejected_notifies_candidate(self, mock_rt, mock_fb):
        from apps.communications.event_handlers import on_application_rejected
        candidate_id = uuid.uuid4()
        app = _mock_app()
        on_application_rejected(sender=None, application=app, candidate_user_id=candidate_id)
        n = Notification.objects.filter(
            user_id=candidate_id,
            notification_type='application.rejected',
        ).first()
        self.assertIsNotNone(n)

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_no_crash_if_application_missing(self, mock_rt, mock_fb):
        from apps.communications.event_handlers import on_application_submitted
        # Should not raise — just silently no-op
        on_application_submitted(sender=None, application=None)


class TestInterviewEventHandlers(TestCase):
    """
    Interview signal tests use disconnect/reconnect to isolate from other
    signal receivers (e.g., automation module) that expect real model instances.
    """

    def _send_interview_signal_isolated(self, signal, **kwargs):
        """Send signal to only our communications receivers, not automation."""
        from apps.communications import event_handlers
        # Call our handlers directly to avoid cross-module side effects in tests
        for receiver_func, _ in signal.receivers:
            try:
                from django.dispatch.dispatcher import _make_id
                receiver_func(signal=signal, sender=None, **kwargs)
            except Exception:
                pass

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_interview_scheduled_notifies_candidate_and_interviewers(self, mock_rt, mock_fb):
        candidate_id = uuid.uuid4()
        interviewer1 = uuid.uuid4()
        interviewer2 = uuid.uuid4()
        interview = _mock_interview()

        from apps.communications.event_handlers import on_interview_scheduled
        on_interview_scheduled(
            sender=None,
            interview=interview,
            candidate_user_id=candidate_id,
            interviewer_user_ids=[interviewer1, interviewer2],
        )

        for uid in [candidate_id, interviewer1, interviewer2]:
            n = Notification.objects.filter(
                user_id=uid,
                notification_type='interview.scheduled',
            ).first()
            self.assertIsNotNone(n, f'Notification missing for user {uid}')
            self.assertEqual(n.severity, NotificationSeverity.HIGH)

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_interview_completed_notifies_recruiter(self, mock_rt, mock_fb):
        recruiter_id = uuid.uuid4()
        interview = _mock_interview()
        from apps.communications.event_handlers import on_interview_completed
        on_interview_completed(
            sender=None,
            interview=interview,
            recruiter_user_id=recruiter_id,
        )
        n = Notification.objects.filter(
            user_id=recruiter_id,
            notification_type='interview.feedback_pending',
        ).first()
        self.assertIsNotNone(n)

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_interview_cancelled_notifies_candidate(self, mock_rt, mock_fb):
        candidate_id = uuid.uuid4()
        interview = _mock_interview()
        from apps.communications.event_handlers import on_interview_cancelled
        on_interview_cancelled(
            sender=None,
            interview=interview,
            candidate_user_id=candidate_id,
        )
        n = Notification.objects.filter(
            user_id=candidate_id,
            notification_type='interview.cancelled',
        ).first()
        self.assertIsNotNone(n)
        self.assertEqual(n.severity, NotificationSeverity.HIGH)


class TestPassportEventHandlers(TestCase):

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_passport_viewed_notifies_candidate(self, mock_rt, mock_fb):
        from apps.communications.event_handlers import on_passport_viewed
        candidate_id = uuid.uuid4()
        on_passport_viewed(sender=None, candidate_user_id=candidate_id, viewer_name='ACME Corp')
        n = Notification.objects.filter(
            user_id=candidate_id,
            notification_type='passport.viewed',
        ).first()
        self.assertIsNotNone(n)
        self.assertIn('ACME Corp', n.body)


class TestDeadlineEventHandlers(TestCase):

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_deadline_overdue_sends_critical_notification(self, mock_rt, mock_fb):
        from apps.communications.event_handlers import on_deadline_overdue
        owner_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        on_deadline_overdue(
            sender=None,
            owner_user_id=owner_id,
            entity_type='job',
            entity_id=uuid.uuid4(),
            deadline_label='Offer deadline',
            tenant_id=tenant_id,
        )
        n = Notification.objects.filter(
            user_id=owner_id,
            notification_type='deadline.overdue',
        ).first()
        self.assertIsNotNone(n)
        self.assertEqual(n.severity, NotificationSeverity.CRITICAL)
