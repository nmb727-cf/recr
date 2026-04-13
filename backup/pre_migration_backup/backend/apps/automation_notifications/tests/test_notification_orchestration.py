"""
Automation Notification Orchestration — test suite

Covers the 5 acceptance tests from the spec plus additional edge cases.
"""
import uuid
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.automation_notifications.models import (
    DeliveryStatus,
    EscalationStatus,
    NotificationChannel,
    WorkflowEscalationNotification,
    WorkflowNotificationDelivery,
    WorkflowNotificationPreference,
    WorkflowNotificationRule,
)
from apps.automation_notifications.services.workflow_notification_orchestrator import (
    WorkflowNotificationOrchestrator as WNO,
)
from apps.automation_notifications.views import (
    DeliveryLogView,
    NotificationRuleListView,
    RetryDeliveryView,
)

TENANT_ID    = uuid.UUID('00000000-0000-0000-0000-000000000001')
WORKFLOW_ID  = uuid.UUID('00000000-0000-0000-0000-000000000010')
EXECUTION_ID = uuid.UUID('00000000-0000-0000-0000-000000000020')


def _user(role: str) -> CustomUser:
    email = f'{role}-notif@example.com'
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return CustomUser.objects.create_user(
            email=email, password='testpass123', role=role, tenant_id=TENANT_ID,
        )


def _make_rule(**kwargs) -> WorkflowNotificationRule:
    defaults = dict(
        tenant_id=TENANT_ID,
        workflow_id=WORKFLOW_ID,
        notification_event='candidate.reminder',
        recipient_type='candidate',
        channel=NotificationChannel.IN_APP,
        fallback_channels=[NotificationChannel.EMAIL],
        throttle_window_minutes=0,
        dedupe_key_template='',
        is_active=True,
    )
    defaults.update(kwargs)
    return WorkflowNotificationRule.objects.create(**defaults)


def _candidate_context():
    return {
        'candidate_id': str(uuid.uuid4()),
        'candidate_email': 'candidate@example.com',
        'candidate_name': 'Test Candidate',
        'job_title': 'Software Engineer',
        'company_name': 'ACME Corp',
        'recruiter_name': 'Jane Recruiter',
    }


# ─── Test 1: Whatsapp dispatch creates delivery record ───────────────────────

class ChannelDispatchTests(TestCase):

    def test_whatsapp_dispatch_creates_delivery(self):
        """
        Workflow sends candidate reminder via whatsapp → delivery record created.
        """
        rule = _make_rule(
            channel=NotificationChannel.WHATSAPP,
            fallback_channels=[NotificationChannel.EMAIL],
        )
        ctx = _candidate_context()
        ctx['candidate_phone'] = '+919876543210'

        with patch.object(WNO, '_send_whatsapp', return_value={'message_id': 'wa_test_001'}):
            result = WNO.dispatch(
                tenant_id=TENANT_ID,
                execution_id=EXECUTION_ID,
                workflow_id=WORKFLOW_ID,
                rule=rule,
                context={**ctx, 'candidate_user_id': None},
                recipient_override={'email': '', 'phone': '+919876543210', 'user_id': None},
            )

        self.assertEqual(result['status'], 'dispatched')
        delivery = WorkflowNotificationDelivery.objects.filter(
            tenant_id=TENANT_ID, channel=NotificationChannel.WHATSAPP
        ).first()
        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.status, DeliveryStatus.SENT)

    # ─── Test 2: Whatsapp failure triggers email fallback ─────────────────────

    def test_whatsapp_failure_triggers_email_fallback(self):
        """
        WhatsApp delivery fails after retries exhausted → fallback email queued and sent.
        """
        from apps.automation_notifications.services.workflow_notification_orchestrator import MAX_RETRIES

        rule = _make_rule(
            channel=NotificationChannel.WHATSAPP,
            fallback_channels=[NotificationChannel.EMAIL],
        )
        # Pre-seed a delivery that has already used up all retries
        delivery = WorkflowNotificationDelivery.objects.create(
            tenant_id=TENANT_ID,
            execution_id=EXECUTION_ID,
            workflow_id=WORKFLOW_ID,
            notification_rule=rule,
            recipient_email='candidate@example.com',
            recipient_phone='+91000',
            channel=NotificationChannel.WHATSAPP,
            status=DeliveryStatus.QUEUED,
            subject='Test WA',
            rendered_message='Hi there',
            retry_count=MAX_RETRIES - 1,  # one more failure exhausts retries
        )

        with patch.object(WNO, '_send_whatsapp', side_effect=RuntimeError('WA provider down')):
            with patch.object(WNO, '_send_email', return_value={'message_id': 'email_fallback_001'}):
                WNO.send_notification(delivery)

        # Email fallback delivery should exist
        fallback = WorkflowNotificationDelivery.objects.filter(
            tenant_id=TENANT_ID,
            channel=NotificationChannel.EMAIL,
        ).filter(metadata__fallback_from=NotificationChannel.WHATSAPP).first()
        self.assertIsNotNone(fallback)

    # ─── Test 3: Throttle window suppresses duplicate ─────────────────────────

    def test_throttle_suppresses_second_send(self):
        """
        Two workflows send same reminder within throttle window →
        second send skipped as throttled or deduplicated.
        """
        rule = _make_rule(
            channel=NotificationChannel.IN_APP,
            throttle_window_minutes=1440,   # 24 hours
        )
        recipient  = {'user_id': str(uuid.uuid4()), 'email': '', 'phone': ''}
        ctx        = _candidate_context()
        ctx['candidate_user_id'] = recipient['user_id']

        with patch.object(WNO, '_send_in_app', return_value={'message_id': 'inapp_001'}):
            first = WNO.dispatch(
                tenant_id=TENANT_ID, execution_id=EXECUTION_ID, workflow_id=WORKFLOW_ID,
                rule=rule, context=ctx, recipient_override=recipient,
            )

        # Second dispatch within throttle window
        second = WNO.dispatch(
            tenant_id=TENANT_ID, execution_id=EXECUTION_ID, workflow_id=WORKFLOW_ID,
            rule=rule, context=ctx, recipient_override=recipient,
        )

        results = second.get('results', [])
        self.assertTrue(
            any(r.get('status') in ('throttled', 'deduplicated') for r in results),
            f'Expected throttled/deduplicated, got: {results}',
        )

    # ─── Test 4: Quiet hours delays / reroutes ────────────────────────────────

    def test_quiet_hours_blocks_channel(self):
        """
        Recipient quiet hours active → channel reported as unavailable.
        """
        uid = uuid.uuid4()
        # Set quiet hours covering the entire day
        WorkflowNotificationPreference.objects.create(
            tenant_id=TENANT_ID,
            user_id=uid,
            notification_type='candidate.reminder',
            preferred_channels=[NotificationChannel.IN_APP],
            quiet_hours_start=__import__('datetime').time(0, 0),
            quiet_hours_end=__import__('datetime').time(23, 59),
            allow_escalation_override=False,
            is_active=True,
        )
        rule = _make_rule(channel=NotificationChannel.IN_APP, fallback_channels=[])
        # Channel should be blocked by quiet hours
        result = WNO._is_channel_available(NotificationChannel.IN_APP, user_id=uid)
        self.assertFalse(result)

    def test_escalation_override_bypasses_quiet_hours(self):
        """
        allow_escalation_override=True → quiet hours do not block escalations.
        """
        uid = uuid.uuid4()
        WorkflowNotificationPreference.objects.create(
            tenant_id=TENANT_ID,
            user_id=uid,
            notification_type='candidate.reminder',
            preferred_channels=[NotificationChannel.EMAIL],
            quiet_hours_start=__import__('datetime').time(0, 0),
            quiet_hours_end=__import__('datetime').time(23, 59),
            allow_escalation_override=True,
            is_active=True,
        )
        # Escalation should NOT be blocked
        in_quiet = WNO._is_in_quiet_hours(uid, escalation=True)
        self.assertFalse(in_quiet)

    # ─── Test 5: Escalation notification ─────────────────────────────────────

    def test_no_response_triggers_escalation(self):
        """
        No response after threshold → escalation notification sent to next responsible user.
        """
        ctx = {
            **_candidate_context(),
            'recruiter_manager_id': str(uuid.uuid4()),
            'recruiter_manager_email': 'manager@example.com',
        }

        with patch.object(WNO, '_send_email', return_value={'message_id': 'esc_email_001'}):
            result = WNO.send_escalation_notification(
                tenant_id=TENANT_ID,
                workflow_id=WORKFLOW_ID,
                execution_id=EXECUTION_ID,
                reason='No response in 48 hours',
                context=ctx,
                level=1,
            )

        self.assertEqual(result['status'], 'escalation_sent')
        self.assertGreater(result['recipients'], 0)

        escalation = WorkflowEscalationNotification.objects.filter(
            tenant_id=TENANT_ID, trigger_reason='No response in 48 hours'
        ).first()
        self.assertIsNotNone(escalation)
        self.assertEqual(escalation.status, EscalationStatus.SENT)


# ─── API-level tests ──────────────────────────────────────────────────────────

class NotificationRuleAPITests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin   = _user('tenant_admin')
        self.manager = _user('hr_manager')
        self.viewer  = _user('viewer')

    def test_admin_can_create_rule(self):
        request = self.factory.post(
            '/api/v1/workflow-notifications/rules/',
            {
                'workflow_id': str(WORKFLOW_ID),
                'notification_event': 'interview.scheduled',
                'recipient_type': 'candidate',
                'channel': 'email',
                'fallback_channels': ['in_app'],
                'throttle_window_minutes': 1440,
                'is_active': True,
            },
            format='json',
        )
        force_authenticate(request, user=self.admin)
        response = NotificationRuleListView.as_view()(request)
        self.assertEqual(response.status_code, 201)

    def test_viewer_cannot_create_rule(self):
        request = self.factory.post(
            '/api/v1/workflow-notifications/rules/',
            {'workflow_id': str(WORKFLOW_ID), 'notification_event': 'test'},
            format='json',
        )
        force_authenticate(request, user=self.viewer)
        response = NotificationRuleListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_deliveries(self):
        request = self.factory.get('/api/v1/workflow-notifications/deliveries/')
        force_authenticate(request, user=self.admin)
        response = DeliveryLogView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_retry_failed_delivery(self):
        rule = _make_rule()
        delivery = WorkflowNotificationDelivery.objects.create(
            tenant_id=TENANT_ID,
            channel=NotificationChannel.IN_APP,
            recipient_user_id=uuid.uuid4(),
            status=DeliveryStatus.FAILED,
            subject='Test retry',
            rendered_message='Retry me',
        )
        request = self.factory.post(f'/api/v1/workflow-notifications/retry/{delivery.id}/')
        force_authenticate(request, user=self.admin)
        with patch.object(WNO, '_send_in_app', return_value={'message_id': 'retried_001'}):
            response = RetryDeliveryView.as_view()(request, delivery_id=delivery.id)
        self.assertEqual(response.status_code, 200)

    def test_render_notification_uses_placeholders(self):
        rule = _make_rule()
        ctx  = {'candidate_name': 'Alice', 'job_title': 'Backend Engineer', 'company_name': 'ACME'}
        subject, body = WNO.render_notification(rule, ctx)
        self.assertIn('Alice', body)

    def test_channel_health_returns_all_channels(self):
        health = WNO.get_channel_health(TENANT_ID)
        self.assertIn('email', health)
        self.assertIn('in_app', health)
        self.assertIn('whatsapp', health)
