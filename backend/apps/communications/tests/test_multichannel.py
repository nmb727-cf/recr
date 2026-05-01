"""
Multi-Channel Communication Engine — Test Suite
================================================
Tests cover:

1.  Channel plan resolution (priority-based defaults)
2.  Tenant with email only does not schedule WhatsApp/SMS
3.  Tenant with WhatsApp enabled CAN send WhatsApp fallback
4.  SMS escalation fires only when configured
5.  Disabled channel is suppressed gracefully
6.  CommunicationDelivery record created correctly
7.  Retry logic is idempotent
8.  Notification read cancels pending channel deliveries
9.  Multi-tenant isolation — delivery A cannot see delivery B
10. Missing recipient identifier creates SKIPPED delivery
11. Template rendering differs correctly by channel
12. Provider failure does not crash orchestration flow
13. WhatsApp normalisation: phone numbers converted to E.164
14. SMS body truncated to safe limit
15. Push provider placeholder gracefully skips
"""
import uuid
from unittest.mock import MagicMock, patch

from django.test import TestCase

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uuid():
    return uuid.uuid4()


class MockNotification:
    """Minimal Notification stand-in for testing."""
    def __init__(self, *, title='Test', body='Body text', action_url='', severity='high',
                 is_read=False, notification_type='interview.scheduled'):
        self.id = _uuid()
        self.tenant_id = _uuid()
        self.user_id = _uuid()
        self.title = title
        self.body = body
        self.action_url = action_url
        self.severity = severity
        self.is_read = is_read
        self._type = notification_type

    def get_type(self):
        return self._type


class MockRule:
    """Minimal NotificationRule stand-in."""
    def __init__(self, **kwargs):
        self.is_active          = kwargs.get('is_active', True)
        self.priority           = kwargs.get('priority', 'high')
        self.in_app_enabled     = kwargs.get('in_app_enabled', True)
        self.email_enabled      = kwargs.get('email_enabled', True)
        self.whatsapp_enabled   = kwargs.get('whatsapp_enabled', False)
        self.sms_enabled        = kwargs.get('sms_enabled', False)
        self.fallback_enabled   = kwargs.get('fallback_enabled', True)
        self.fallback_delay_minutes = kwargs.get('fallback_delay_minutes', 10)
        self.escalation_enabled = kwargs.get('escalation_enabled', False)
        self.escalation_delay_minutes = kwargs.get('escalation_delay_minutes', 60)
        self.escalation_target_type = kwargs.get('escalation_target_type', 'tenant_admin')


# ===========================================================================
# 1. Channel plan resolution — priority defaults
# ===========================================================================

class TestChannelPlanResolution(TestCase):

    def _plan(self, priority, rule=None):
        from apps.communications.channel_routing import resolve_channel_plan
        return resolve_channel_plan(
            tenant_id=_uuid(),
            event_key='interview.scheduled',
            priority=priority,
            rule_config=rule,
        )

    def test_low_priority_gives_in_app_only(self):
        plan = self._plan('low')
        immediate_types = [s.channel_type for s in plan.immediate_channels if not s.suppressed]
        self.assertIn('in_app', immediate_types)
        self.assertNotIn('whatsapp', immediate_types)
        self.assertNotIn('sms', immediate_types)
        self.assertFalse(plan.has_fallback)

    def test_medium_priority_gives_email_fallback(self):
        plan = self._plan('medium')
        immediate_types = [s.channel_type for s in plan.immediate_channels if not s.suppressed]
        self.assertIn('in_app', immediate_types)
        # medium priority has 40 min fallback delay configured
        self.assertEqual(plan.fallback_delay_seconds, 2400)

    def test_high_priority_gives_whatsapp_fallback(self):
        rule = MockRule(
            priority='high',
            whatsapp_enabled=True,
            fallback_enabled=True,
            fallback_delay_minutes=10,
        )
        with patch(
            'apps.communications.channel_routing._check_tenant_channel_availability',
            return_value={'in_app': True, 'email': True, 'whatsapp': True, 'sms': False, 'push': False},
        ):
            plan = self._plan('high', rule=rule)
        fallback_types = [s.channel_type for s in plan.fallback_channels if not s.suppressed]
        self.assertIn('whatsapp', fallback_types)

    def test_critical_priority_has_sms_escalation(self):
        rule = MockRule(
            priority='critical',
            whatsapp_enabled=True,
            sms_enabled=True,
            fallback_enabled=True,
            fallback_delay_minutes=1,
            escalation_enabled=True,
            escalation_delay_minutes=5,
        )
        with patch(
            'apps.communications.channel_routing._check_tenant_channel_availability',
            return_value={'in_app': True, 'email': True, 'whatsapp': True, 'sms': True, 'push': False},
        ):
            plan = self._plan('critical', rule=rule)
        escalation_types = [s.channel_type for s in plan.escalation_channels if not s.suppressed]
        self.assertIn('sms', escalation_types)

    def test_unknown_priority_defaults_to_medium(self):
        from apps.communications.channel_routing import resolve_channel_plan
        plan = resolve_channel_plan(
            tenant_id=_uuid(),
            event_key='test',
            priority='unknown_value',
        )
        self.assertEqual(plan.priority, 'medium')


# ===========================================================================
# 2. Tenant with email only — WhatsApp/SMS suppressed
# ===========================================================================

class TestTenantEmailOnly(TestCase):

    def test_whatsapp_suppressed_when_not_globally_enabled(self):
        from apps.communications.channel_routing import resolve_channel_plan
        rule = MockRule(priority='high', whatsapp_enabled=True, fallback_enabled=True)
        tenant_id = _uuid()

        # Tenant has WhatsApp disabled at the global setting level
        with patch(
            'apps.communications.channel_routing._check_tenant_channel_availability',
            return_value={'in_app': True, 'email': True, 'whatsapp': False, 'sms': False, 'push': False},
        ):
            plan = resolve_channel_plan(
                tenant_id=tenant_id,
                event_key='interview.scheduled',
                priority='high',
                rule_config=rule,
            )

        suppressed_types = [s.channel_type for s in plan.suppressed_channels]
        self.assertIn('whatsapp', suppressed_types)

        # Fallback channels should be empty or whatsapp should not appear in active fallback
        active_fallback = [s.channel_type for s in plan.fallback_channels if not s.suppressed]
        self.assertNotIn('whatsapp', active_fallback)

    def test_sms_suppressed_when_not_globally_enabled(self):
        from apps.communications.channel_routing import resolve_channel_plan
        rule = MockRule(priority='critical', sms_enabled=True, escalation_enabled=True)

        with patch(
            'apps.communications.channel_routing._check_tenant_channel_availability',
            return_value={'in_app': True, 'email': True, 'whatsapp': False, 'sms': False, 'push': False},
        ):
            plan = resolve_channel_plan(
                tenant_id=_uuid(),
                event_key='deadline.overdue',
                priority='critical',
                rule_config=rule,
            )

        active_escalation = [s.channel_type for s in plan.escalation_channels if not s.suppressed]
        self.assertNotIn('sms', active_escalation)


# ===========================================================================
# 3. Tenant with WhatsApp enabled CAN send WhatsApp fallback
# ===========================================================================

class TestWhatsAppEnabled(TestCase):

    def test_whatsapp_in_fallback_when_enabled(self):
        from apps.communications.channel_routing import resolve_channel_plan
        rule = MockRule(
            priority='high',
            whatsapp_enabled=True,
            fallback_enabled=True,
            fallback_delay_minutes=10,
        )
        with patch(
            'apps.communications.channel_routing._check_tenant_channel_availability',
            return_value={'in_app': True, 'email': True, 'whatsapp': True, 'sms': False, 'push': False},
        ):
            plan = resolve_channel_plan(
                tenant_id=_uuid(),
                event_key='interview.scheduled',
                priority='high',
                rule_config=rule,
            )

        active_fallback = [s.channel_type for s in plan.fallback_channels if not s.suppressed]
        self.assertIn('whatsapp', active_fallback)
        self.assertEqual(plan.fallback_delay_seconds, 600)


# ===========================================================================
# 4. SMS escalation fires only when configured
# ===========================================================================

class TestSMSEscalation(TestCase):

    def test_sms_not_added_when_escalation_disabled(self):
        from apps.communications.channel_routing import resolve_channel_plan
        rule = MockRule(priority='critical', sms_enabled=True, escalation_enabled=False)

        with patch(
            'apps.communications.channel_routing._check_tenant_channel_availability',
            return_value={'in_app': True, 'email': True, 'whatsapp': True, 'sms': True, 'push': False},
        ):
            plan = resolve_channel_plan(
                tenant_id=_uuid(),
                event_key='deadline.overdue',
                priority='critical',
                rule_config=rule,
            )

        escalation_types = [s.channel_type for s in plan.escalation_channels if not s.suppressed]
        self.assertNotIn('sms', escalation_types)

    def test_sms_added_when_escalation_enabled(self):
        from apps.communications.channel_routing import resolve_channel_plan
        rule = MockRule(
            priority='critical',
            sms_enabled=True,
            escalation_enabled=True,
            escalation_delay_minutes=5,
        )
        with patch(
            'apps.communications.channel_routing._check_tenant_channel_availability',
            return_value={'in_app': True, 'email': True, 'whatsapp': True, 'sms': True, 'push': False},
        ):
            plan = resolve_channel_plan(
                tenant_id=_uuid(),
                event_key='deadline.overdue',
                priority='critical',
                rule_config=rule,
            )

        escalation_types = [s.channel_type for s in plan.escalation_channels if not s.suppressed]
        self.assertIn('sms', escalation_types)
        self.assertEqual(plan.escalation_delay_seconds, 300)


# ===========================================================================
# 5. Disabled channel suppressed gracefully (no exception)
# ===========================================================================

class TestDisabledChannelSuppressed(TestCase):

    def test_suppression_does_not_raise(self):
        from apps.communications.channel_routing import resolve_channel_plan

        rule = MockRule(priority='high', whatsapp_enabled=True, fallback_enabled=True)
        with patch(
            'apps.communications.channel_routing._check_tenant_channel_availability',
            return_value={},  # All missing → default True for in_app/email, False for rest
        ):
            try:
                plan = resolve_channel_plan(
                    tenant_id=_uuid(),
                    event_key='test.event',
                    priority='high',
                    rule_config=rule,
                )
            except Exception as exc:
                self.fail(f'resolve_channel_plan raised unexpectedly: {exc}')

    def test_all_channels_off_still_returns_in_app(self):
        from apps.communications.channel_routing import resolve_channel_plan
        with patch(
            'apps.communications.channel_routing._check_tenant_channel_availability',
            return_value={'in_app': True, 'email': False, 'whatsapp': False, 'sms': False},
        ):
            plan = resolve_channel_plan(
                tenant_id=_uuid(),
                event_key='test',
                priority='medium',
            )
        active = [s.channel_type for s in plan.immediate_channels if not s.suppressed]
        self.assertIn('in_app', active)


# ===========================================================================
# 6. CommunicationDelivery created correctly
# ===========================================================================

class TestDeliveryRecordCreation(TestCase):

    @patch('apps.communications.channel_tasks.send_channel_delivery_task')
    def test_delivery_record_created_pending(self, mock_task):
        from apps.communications.channel_services import send_via_channel
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )

        mock_task.apply_async = MagicMock()

        tenant_id = _uuid()
        notification = MockNotification()
        notification.tenant_id = tenant_id

        delivery = send_via_channel(
            tenant_id=tenant_id,
            channel_type='whatsapp',
            recipient_identifier='+919876543210',
            recipient_user_id=_uuid(),
            notification_id=notification.id,
            event_key='interview.scheduled',
            priority='high',
            notification=notification,
            schedule_async=True,
        )

        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.channel_type, 'whatsapp')
        self.assertEqual(delivery.status, CommunicationDeliveryStatus.PENDING)
        self.assertEqual(delivery.recipient_identifier, '+919876543210')
        mock_task.apply_async.assert_called_once()


# ===========================================================================
# 7. Retry logic is idempotent
# ===========================================================================

class TestRetryIdempotency(TestCase):

    @patch('apps.communications.channel_services.resolve_channel_provider')
    def test_already_sent_delivery_not_re_executed(self, mock_resolve):
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )
        from apps.communications.channel_services import execute_channel_delivery

        tenant_id = _uuid()
        delivery = CommunicationDelivery.objects.create(
            tenant_id=tenant_id,
            channel_type='whatsapp',
            recipient_identifier='+919876543210',
            status=CommunicationDeliveryStatus.SENT,
        )

        result = execute_channel_delivery(str(delivery.id))

        # Provider should NOT be called for an already-sent delivery
        mock_resolve.assert_not_called()
        # Result is True because SENT is success
        self.assertTrue(result)

    @patch('apps.communications.channel_services.resolve_channel_provider')
    def test_cancelled_delivery_not_re_executed(self, mock_resolve):
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )
        from apps.communications.channel_services import execute_channel_delivery

        delivery = CommunicationDelivery.objects.create(
            tenant_id=_uuid(),
            channel_type='sms',
            recipient_identifier='+919876543210',
            status=CommunicationDeliveryStatus.CANCELLED,
        )
        result = execute_channel_delivery(str(delivery.id))
        mock_resolve.assert_not_called()
        self.assertFalse(result)


# ===========================================================================
# 8. Notification read cancels pending channel deliveries
# ===========================================================================

class TestCancellationOnRead(TestCase):

    def test_cancel_channel_fallbacks_marks_pending_as_cancelled(self):
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )
        from apps.communications.channel_services import cancel_channel_fallbacks

        tenant_id = _uuid()
        notification_id = _uuid()

        # Create 2 pending deliveries for this notification
        d1 = CommunicationDelivery.objects.create(
            tenant_id=tenant_id,
            notification_id=notification_id,
            channel_type='whatsapp',
            recipient_identifier='+919876543210',
            status=CommunicationDeliveryStatus.PENDING,
        )
        d2 = CommunicationDelivery.objects.create(
            tenant_id=tenant_id,
            notification_id=notification_id,
            channel_type='sms',
            recipient_identifier='+919876543210',
            status=CommunicationDeliveryStatus.PENDING,
        )
        # One already sent — should NOT be touched
        d3 = CommunicationDelivery.objects.create(
            tenant_id=tenant_id,
            notification_id=notification_id,
            channel_type='push',
            recipient_identifier='push_token_abc',
            status=CommunicationDeliveryStatus.SENT,
        )

        count = cancel_channel_fallbacks(notification_id=notification_id, reason='notification_read')

        self.assertEqual(count, 2)
        d1.refresh_from_db()
        d2.refresh_from_db()
        d3.refresh_from_db()
        self.assertEqual(d1.status, CommunicationDeliveryStatus.CANCELLED)
        self.assertEqual(d2.status, CommunicationDeliveryStatus.CANCELLED)
        self.assertEqual(d3.status, CommunicationDeliveryStatus.SENT)  # untouched


# ===========================================================================
# 9. Multi-tenant isolation
# ===========================================================================

class TestMultiTenantIsolation(TestCase):

    def test_get_active_config_isolated_by_tenant(self):
        from apps.communications.channel_config_models import TenantChannelConfig
        from apps.communications.utils import encrypt_string

        tenant_a = _uuid()
        tenant_b = _uuid()

        TenantChannelConfig.objects.create(
            tenant_id=tenant_a,
            channel_type='whatsapp',
            provider='mock',
            api_token_encrypted=encrypt_string('token_a'),
        )
        TenantChannelConfig.objects.create(
            tenant_id=tenant_b,
            channel_type='whatsapp',
            provider='mock',
            api_token_encrypted=encrypt_string('token_b'),
        )

        cfg_a = TenantChannelConfig.get_active(tenant_a, 'whatsapp')
        cfg_b = TenantChannelConfig.get_active(tenant_b, 'whatsapp')

        self.assertIsNotNone(cfg_a)
        self.assertIsNotNone(cfg_b)
        self.assertNotEqual(cfg_a.id, cfg_b.id)
        self.assertEqual(cfg_a.decrypted_api_token, 'token_a')
        self.assertEqual(cfg_b.decrypted_api_token, 'token_b')

    def test_delivery_query_isolated_by_tenant(self):
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )

        tenant_a = _uuid()
        tenant_b = _uuid()

        CommunicationDelivery.objects.create(
            tenant_id=tenant_a,
            channel_type='sms',
            recipient_identifier='+919000000001',
            status=CommunicationDeliveryStatus.SENT,
        )
        CommunicationDelivery.objects.create(
            tenant_id=tenant_b,
            channel_type='sms',
            recipient_identifier='+919000000002',
            status=CommunicationDeliveryStatus.SENT,
        )

        a_deliveries = CommunicationDelivery.objects.filter(tenant_id=tenant_a)
        b_deliveries = CommunicationDelivery.objects.filter(tenant_id=tenant_b)
        self.assertEqual(a_deliveries.count(), 1)
        self.assertEqual(b_deliveries.count(), 1)
        self.assertNotEqual(
            a_deliveries.first().recipient_identifier,
            b_deliveries.first().recipient_identifier,
        )


# ===========================================================================
# 10. Missing recipient identifier creates SKIPPED delivery
# ===========================================================================

class TestMissingRecipientSkipped(TestCase):

    @patch('apps.communications.channel_tasks.send_channel_delivery_task')
    def test_empty_phone_creates_skipped_delivery(self, mock_task):
        from apps.communications.channel_services import send_via_channel
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )

        delivery = send_via_channel(
            tenant_id=_uuid(),
            channel_type='whatsapp',
            recipient_identifier='',        # Empty
            recipient_user_id=_uuid(),
            event_key='interview.scheduled',
        )

        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.status, CommunicationDeliveryStatus.SKIPPED)
        self.assertEqual(delivery.skip_reason, 'no_recipient_identifier')
        mock_task.apply_async.assert_not_called()

    def test_invalid_phone_normalized_to_empty(self):
        from apps.communications.channel_services import normalize_recipient_for_channel
        self.assertEqual(normalize_recipient_for_channel(channel_type='whatsapp', identifier='abc'), '')
        self.assertEqual(normalize_recipient_for_channel(channel_type='sms', identifier='123'), '')
        self.assertEqual(normalize_recipient_for_channel(channel_type='whatsapp', identifier='+919876543210'), '+919876543210')

    def test_valid_push_token_accepted(self):
        from apps.communications.channel_services import normalize_recipient_for_channel
        token = 'APA91bHPRgkF-IZlFTuU7p_0lhEiSX1234567890'
        self.assertEqual(
            normalize_recipient_for_channel(channel_type='push', identifier=token),
            token,
        )


# ===========================================================================
# 11. Template rendering differs by channel
# ===========================================================================

class TestChannelTemplateRendering(TestCase):

    def test_sms_body_truncated_to_limit(self):
        from apps.communications.channel_template_service import render_channel_template

        long_body = 'A' * 500
        notification = MockNotification(body=long_body)
        result = render_channel_template(
            channel_type='sms',
            notification=notification,
        )
        self.assertLessEqual(len(result.body), 307)  # 306 + truncation marker
        self.assertTrue(result.truncated)

    def test_push_title_truncated(self):
        from apps.communications.channel_template_service import render_channel_template

        notification = MockNotification(title='A' * 100, body='Short body')
        result = render_channel_template(
            channel_type='push',
            notification=notification,
        )
        self.assertLessEqual(len(result.subject), 66)
        self.assertTrue(result.truncated)

    def test_whatsapp_with_template_name_returns_params(self):
        from apps.communications.channel_template_service import (
            render_channel_template,
            ChannelTemplate,
        )

        template = ChannelTemplate(
            channel_type='whatsapp',
            template_name='interview_scheduled_v2',
            body_template='Hi {candidate_name}, your interview is at {time}.',
            template_params_keys=['candidate_name', 'time'],
        )
        result = render_channel_template(
            channel_type='whatsapp',
            template=template,
            context={'candidate_name': 'Anjali', 'time': '2pm'},
        )
        self.assertEqual(result.template_name, 'interview_scheduled_v2')
        self.assertEqual(result.template_params['candidate_name'], 'Anjali')

    def test_whatsapp_missing_variable_gives_empty_string(self):
        from apps.communications.channel_template_service import (
            render_channel_template,
            ChannelTemplate,
        )

        template = ChannelTemplate(
            channel_type='whatsapp',
            template_name='test_template',
            body_template='Hello {missing_var}!',
            template_params_keys=['missing_var'],
        )
        result = render_channel_template(
            channel_type='whatsapp',
            template=template,
            context={},
        )
        self.assertIn('missing_var', result.missing_variables)
        # Should not raise
        self.assertEqual(result.template_params.get('missing_var', ''), '')

    def test_in_app_full_body_not_truncated(self):
        from apps.communications.channel_template_service import render_channel_template

        long_body = 'B' * 2000
        notification = MockNotification(body=long_body)
        result = render_channel_template(
            channel_type='in_app',
            notification=notification,
        )
        self.assertEqual(len(result.body), 2000)
        self.assertFalse(result.truncated)

    def test_sms_html_stripped(self):
        from apps.communications.channel_template_service import render_channel_template

        notification = MockNotification(body='<b>Hello</b> <em>world</em>')
        result = render_channel_template(channel_type='sms', notification=notification)
        self.assertNotIn('<b>', result.body)
        self.assertIn('Hello', result.body)


# ===========================================================================
# 12. Provider failure does not crash orchestration
# ===========================================================================

class TestProviderFailureSafety(TestCase):

    @patch('apps.communications.channel_services.resolve_channel_provider')
    def test_provider_send_error_marks_delivery_failed(self, mock_resolve):
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )
        from apps.communications.providers.base import ProviderSendError
        from apps.communications.channel_services import execute_channel_delivery

        mock_provider = MagicMock()
        mock_provider.send.side_effect = ProviderSendError('Invalid phone number', retryable=False)
        mock_resolve.return_value = mock_provider

        delivery = CommunicationDelivery.objects.create(
            tenant_id=_uuid(),
            channel_type='whatsapp',
            recipient_identifier='+919876543210',
            rendered_body='Test message',
            status=CommunicationDeliveryStatus.PENDING,
        )

        result = execute_channel_delivery(str(delivery.id))

        self.assertFalse(result)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, CommunicationDeliveryStatus.FAILED)
        self.assertIn('Invalid phone number', delivery.error_message)

    @patch('apps.communications.channel_services.resolve_channel_provider')
    def test_provider_unavailable_marks_delivery_deferred(self, mock_resolve):
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )
        from apps.communications.providers.base import ProviderUnavailableError
        from apps.communications.channel_services import execute_channel_delivery

        mock_provider = MagicMock()
        mock_provider.send.side_effect = ProviderUnavailableError('Gateway timeout')
        mock_resolve.return_value = mock_provider

        delivery = CommunicationDelivery.objects.create(
            tenant_id=_uuid(),
            channel_type='sms',
            recipient_identifier='+919876543210',
            rendered_body='Urgent reminder',
            status=CommunicationDeliveryStatus.PENDING,
            attempt_number=1,
            max_attempts=3,
        )

        with patch('apps.communications.channel_tasks.retry_channel_delivery_task') as mock_retry:
            mock_retry.apply_async = MagicMock()
            result = execute_channel_delivery(str(delivery.id))

        self.assertFalse(result)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, CommunicationDeliveryStatus.DEFERRED)
        self.assertEqual(delivery.attempt_number, 2)

    @patch('apps.communications.channel_services.resolve_channel_provider')
    def test_no_provider_marks_delivery_skipped(self, mock_resolve):
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )
        from apps.communications.channel_services import execute_channel_delivery

        mock_resolve.return_value = None  # No provider configured

        delivery = CommunicationDelivery.objects.create(
            tenant_id=_uuid(),
            channel_type='whatsapp',
            recipient_identifier='+919876543210',
            rendered_body='Test',
            status=CommunicationDeliveryStatus.PENDING,
        )

        result = execute_channel_delivery(str(delivery.id))
        self.assertFalse(result)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, CommunicationDeliveryStatus.SKIPPED)
        self.assertEqual(delivery.skip_reason, 'no_provider_configured')


# ===========================================================================
# 13. Mock WhatsApp provider — send and clear
# ===========================================================================

class TestMockWhatsAppProvider(TestCase):

    def setUp(self):
        from apps.communications.providers.whatsapp.mock import MockWhatsAppProvider
        MockWhatsAppProvider.clear()

    def test_mock_records_send(self):
        from apps.communications.providers.whatsapp.mock import MockWhatsAppProvider

        provider = MockWhatsAppProvider(config={})
        result = provider.send(
            recipient='+919876543210',
            body='Interview confirmed for tomorrow at 10am.',
            template_name='interview_reminder',
            template_params={'candidate_name': 'Ravi', 'time': '10am'},
        )
        self.assertTrue(result.success)
        self.assertNotEqual(result.external_message_id, '')
        self.assertEqual(len(MockWhatsAppProvider.sent_messages), 1)
        self.assertEqual(MockWhatsAppProvider.sent_messages[0]['recipient'], '+919876543210')

    def test_mock_simulates_failure(self):
        from apps.communications.providers.whatsapp.mock import MockWhatsAppProvider
        from apps.communications.providers.base import ProviderSendError

        provider = MockWhatsAppProvider(config={'fail': True})
        with self.assertRaises(ProviderSendError):
            provider.send(recipient='+919876543210', body='Test')

    def test_mock_simulates_unavailable(self):
        from apps.communications.providers.whatsapp.mock import MockWhatsAppProvider
        from apps.communications.providers.base import ProviderUnavailableError

        provider = MockWhatsAppProvider(config={'unavailable': True})
        with self.assertRaises(ProviderUnavailableError):
            provider.send(recipient='+919876543210', body='Test')


# ===========================================================================
# 14. Phone normalisation
# ===========================================================================

class TestPhoneNormalisation(TestCase):

    def test_e164_preserved(self):
        from apps.communications.channel_services import normalize_recipient_for_channel
        self.assertEqual(
            normalize_recipient_for_channel(channel_type='whatsapp', identifier='+919876543210'),
            '+919876543210',
        )

    def test_digits_only_adds_plus(self):
        from apps.communications.channel_services import normalize_recipient_for_channel
        result = normalize_recipient_for_channel(channel_type='sms', identifier='919876543210')
        self.assertTrue(result.startswith('+'))

    def test_too_short_returns_empty(self):
        from apps.communications.channel_services import normalize_recipient_for_channel
        self.assertEqual(
            normalize_recipient_for_channel(channel_type='whatsapp', identifier='+123'),
            '',
        )

    def test_spaces_and_dashes_stripped(self):
        from apps.communications.channel_services import normalize_recipient_for_channel
        result = normalize_recipient_for_channel(
            channel_type='whatsapp', identifier='+91 98765 43210'
        )
        self.assertNotIn(' ', result)
        self.assertEqual(result, '+919876543210')


# ===========================================================================
# 15. Push placeholder skips gracefully
# ===========================================================================

class TestPushProviderPlaceholder(TestCase):

    def test_placeholder_returns_skipped_result(self):
        from apps.communications.providers.push.placeholder import PlaceholderPushProvider

        provider = PlaceholderPushProvider(config={})
        result = provider.send(
            recipient='user_token_abc123',
            body='You have a new interview scheduled.',
            subject='Interview Scheduled',
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, 'push_not_implemented')

    def test_placeholder_health_check_returns_unhealthy(self):
        from apps.communications.providers.push.placeholder import PlaceholderPushProvider

        provider = PlaceholderPushProvider(config={})
        health = provider.health_check()
        self.assertFalse(health.healthy)

    @patch('apps.communications.channel_services.resolve_channel_provider')
    def test_push_delivery_marked_skipped(self, mock_resolve):
        from apps.communications.channel_config_models import (
            CommunicationDelivery,
            CommunicationDeliveryStatus,
        )
        from apps.communications.providers.push.placeholder import PlaceholderPushProvider
        from apps.communications.channel_services import execute_channel_delivery

        mock_resolve.return_value = PlaceholderPushProvider(config={})

        delivery = CommunicationDelivery.objects.create(
            tenant_id=_uuid(),
            channel_type='push',
            recipient_identifier='push_token_xyz',
            rendered_body='New interview scheduled',
            rendered_subject='Interview',
            status=CommunicationDeliveryStatus.PENDING,
        )

        result = execute_channel_delivery(str(delivery.id))
        self.assertFalse(result)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, CommunicationDeliveryStatus.SKIPPED)
        self.assertEqual(delivery.skip_reason, 'push_not_implemented')


# ===========================================================================
# 16. Provider factory resolves correct classes
# ===========================================================================

class TestProviderFactory(TestCase):

    def test_get_whatsapp_business_api_provider(self):
        from apps.communications.providers import get_provider
        from apps.communications.providers.whatsapp.business_api import WhatsAppBusinessAPIProvider

        provider = get_provider(
            channel_type='whatsapp',
            provider_name='whatsapp_business_api',
            config={'api_token': 'tok', 'whatsapp_phone_number_id': 'pid'},
        )
        self.assertIsInstance(provider, WhatsAppBusinessAPIProvider)

    def test_get_twilio_whatsapp_provider(self):
        from apps.communications.providers import get_provider
        from apps.communications.providers.whatsapp.twilio import TwilioWhatsAppProvider

        provider = get_provider(
            channel_type='whatsapp',
            provider_name='twilio_whatsapp',
            config={'api_key_id': 'sid', 'api_token': 'tok', 'sender_identifier': '+15005550006'},
        )
        self.assertIsInstance(provider, TwilioWhatsAppProvider)

    def test_get_mock_sms_provider(self):
        from apps.communications.providers import get_provider
        from apps.communications.providers.sms.mock import MockSMSProvider

        provider = get_provider(
            channel_type='sms',
            provider_name='mock',
            config={},
        )
        self.assertIsInstance(provider, MockSMSProvider)

    def test_unknown_provider_raises_config_error(self):
        from apps.communications.providers import get_provider
        from apps.communications.providers.base import ProviderConfigError

        with self.assertRaises(ProviderConfigError):
            get_provider(channel_type='whatsapp', provider_name='nonexistent_provider', config={})

    def test_unknown_channel_raises_config_error(self):
        from apps.communications.providers import get_provider
        from apps.communications.providers.base import ProviderConfigError

        with self.assertRaises(ProviderConfigError):
            get_provider(channel_type='telegram', provider_name='some_provider', config={})


# ===========================================================================
# 17. TenantChannelConfig credential encryption round-trip
# ===========================================================================

class TestChannelConfigEncryption(TestCase):

    def test_api_token_encrypted_at_rest(self):
        from apps.communications.channel_config_models import TenantChannelConfig
        from apps.communications.utils import encrypt_string

        raw_token = 'EAABsbCS1i'
        cfg = TenantChannelConfig.objects.create(
            tenant_id=_uuid(),
            channel_type='whatsapp',
            provider='whatsapp_business_api',
            api_token_encrypted=encrypt_string(raw_token),
        )
        cfg.refresh_from_db()

        # Stored value should NOT equal the raw token
        self.assertNotEqual(cfg.api_token_encrypted, raw_token)
        # Decrypted value should match
        self.assertEqual(cfg.decrypted_api_token, raw_token)

    def test_masked_token_redacts_middle(self):
        from apps.communications.channel_config_models import TenantChannelConfig
        from apps.communications.utils import encrypt_string

        raw_token = 'EAABsbCS1iHello12345'
        cfg = TenantChannelConfig(
            tenant_id=_uuid(),
            channel_type='whatsapp',
            provider='mock',
            api_token_encrypted=encrypt_string(raw_token),
        )
        masked = cfg.masked_api_token()
        self.assertIn('***', masked)
        self.assertNotEqual(masked, raw_token)
