"""
QA Tests: Email Delivery Engine
=================================
Covers:
  1.  Email send success (SMTP + SendGrid)
  2.  Email failure → retry scheduling
  3.  Template rendering (success, missing variables, raw body fallback)
  4.  Tenant config switching (smtp / sendgrid / system)
  5.  Fallback email flow (send_email_for_notification)
  6.  Retry stop condition (max_retries exhausted)
  7.  Multi-tenant isolation
  8.  Priority queue routing
  9.  Provider health_check / validate_config
  10. EmailDelivery state transitions
  11. EmailDeliveryService._resolve_sender
  12. Renderer HTML sanitization
  13. Observability API endpoints (list, detail, retry, health)
"""
import uuid
from unittest.mock import MagicMock, call, patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

TENANT_A = uuid.uuid4()
TENANT_B = uuid.uuid4()
USER_1   = uuid.uuid4()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tenant_config(tenant_id=None, provider='smtp', **kwargs):
    from apps.communications.email_delivery_models import TenantEmailConfig
    from apps.communications.utils import encrypt_string
    return TenantEmailConfig.objects.create(
        tenant_id=tenant_id or TENANT_A,
        provider=provider,
        from_email=kwargs.get('from_email', 'noreply@test.com'),
        from_name=kwargs.get('from_name', 'Test'),
        smtp_host=kwargs.get('smtp_host', 'smtp.example.com'),
        smtp_port=kwargs.get('smtp_port', 587),
        smtp_username=kwargs.get('smtp_username', 'user@example.com'),
        smtp_password_encrypted=encrypt_string(kwargs.get('smtp_password', 'secret')),
        smtp_use_tls=True,
        sendgrid_api_key_encrypted=encrypt_string(kwargs.get('sendgrid_key', 'SG.test_key')),
        is_active=True,
    )


def _make_delivery(tenant_id=None, status='pending', priority='normal', retry_count=0, max_retries=4):
    from apps.communications.email_delivery_models import EmailDelivery
    return EmailDelivery.objects.create(
        tenant_id=tenant_id or TENANT_A,
        recipient_email='user@example.com',
        subject='Test Email',
        template_used='test.event',
        provider='smtp',
        status=status,
        priority=priority,
        retry_count=retry_count,
        max_retries=max_retries,
        metadata={
            'from_email': 'no-reply@test.com',
            'from_name': 'Test',
            'html_body': '<p>Hello</p>',
            'text_body': 'Hello',
        },
    )


def _make_user(tenant_id=None, role='tenant_admin'):
    """Return a mock user object suitable for authentication checks."""
    user = MagicMock()
    user.is_authenticated = True
    user.tenant_id = tenant_id or TENANT_A
    user.id = USER_1
    user.role = role
    return user


# ---------------------------------------------------------------------------
# 1. Email send success
# ---------------------------------------------------------------------------

class TestEmailSendSuccess(TestCase):

    @patch('apps.communications.email_dispatch.tasks.deliver_email_task.apply_async')
    def test_send_email_creates_delivery_and_queues_task(self, mock_apply):
        from apps.communications.email_delivery_service import EmailDeliveryService
        delivery = EmailDeliveryService.send_email(
            tenant_id=str(TENANT_A),
            recipients=['alice@example.com'],
            subject='Hello',
            html_body='<p>Hi</p>',
            text_body='Hi',
        )
        self.assertEqual(delivery.recipient_email, 'alice@example.com')
        self.assertEqual(delivery.status, 'pending')
        mock_apply.assert_called_once()

    @patch('apps.communications.email_dispatch.tasks.deliver_email_task.apply_async')
    def test_send_to_multiple_recipients_creates_multiple_deliveries(self, mock_apply):
        from apps.communications.email_delivery_service import EmailDeliveryService
        result = EmailDeliveryService.send_email(
            tenant_id=str(TENANT_A),
            recipients=['a@example.com', 'b@example.com', 'c@example.com'],
            subject='Broadcast',
            html_body='<p>Hello</p>',
            text_body='Hello',
        )
        # With multiple recipients, list is returned
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertEqual(mock_apply.call_count, 3)

    @patch('apps.communications.email_dispatch.tasks.deliver_email_task.apply_async')
    def test_empty_recipients_returns_empty_list(self, mock_apply):
        from apps.communications.email_delivery_service import EmailDeliveryService
        result = EmailDeliveryService.send_email(
            tenant_id=str(TENANT_A),
            recipients=[],
            subject='Test',
            html_body='<p>X</p>',
            text_body='X',
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        mock_apply.assert_not_called()

    def test_deliver_email_task_calls_smtp_provider(self):
        delivery = _make_delivery()
        from apps.communications.email_dispatch.providers.base import AutomationSendResult
        with patch(
            'apps.communications.email_dispatch.providers.smtp.SMTPAutomationProvider.send',
            return_value=AutomationSendResult(ok=True, status='sent', provider_message_id='msg-001'),
        ):
            from apps.communications.email_dispatch.tasks import deliver_email_task
            deliver_email_task(str(delivery.id))
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, 'sent')
        self.assertEqual(delivery.provider_message_id, 'msg-001')
        self.assertIsNotNone(delivery.sent_at)


# ---------------------------------------------------------------------------
# 2. Email failure → retry scheduling
# ---------------------------------------------------------------------------

class TestEmailRetryScheduling(TestCase):

    def test_deliver_task_schedules_retry_on_failure(self):
        delivery = _make_delivery()
        from apps.communications.email_dispatch.providers.base import AutomationSendResult
        with patch(
            'apps.communications.email_dispatch.providers.smtp.SMTPAutomationProvider.send',
            return_value=AutomationSendResult(ok=False, status='failed', error='SMTP timeout'),
        ), patch(
            'apps.communications.email_dispatch.tasks.deliver_email_task.apply_async',
        ) as mock_retry:
            from apps.communications.email_dispatch.tasks import deliver_email_task
            deliver_email_task(str(delivery.id))
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, 'deferred')
        self.assertEqual(delivery.retry_count, 1)
        mock_retry.assert_called_once()

    def test_retry_delay_progression(self):
        from apps.communications.email_delivery_service import RETRY_DELAYS
        # Verify the 4-step backoff schedule
        self.assertEqual(RETRY_DELAYS[0], 60)     # 1 min
        self.assertEqual(RETRY_DELAYS[1], 300)    # 5 min
        self.assertEqual(RETRY_DELAYS[2], 900)    # 15 min
        self.assertEqual(RETRY_DELAYS[3], 3600)   # 1 hr

    def test_retry_delay_first_attempt_is_60s(self):
        # status must be 'failed' so can_retry() passes
        delivery = _make_delivery(retry_count=0, status='failed')
        with patch(
            'apps.communications.email_dispatch.tasks.deliver_email_task.apply_async',
        ) as mock_apply:
            from apps.communications.email_delivery_service import EmailDeliveryService
            EmailDeliveryService.schedule_retry(
                delivery_id=str(delivery.id),
                current_retry_count=0,
            )
        call_kwargs = mock_apply.call_args.kwargs
        self.assertEqual(call_kwargs['countdown'], 60)

    def test_retry_delay_second_attempt_is_300s(self):
        delivery = _make_delivery(retry_count=1, status='deferred')
        with patch(
            'apps.communications.email_dispatch.tasks.deliver_email_task.apply_async',
        ) as mock_apply:
            from apps.communications.email_delivery_service import EmailDeliveryService
            EmailDeliveryService.schedule_retry(
                delivery_id=str(delivery.id),
                current_retry_count=1,
            )
        call_kwargs = mock_apply.call_args.kwargs
        self.assertEqual(call_kwargs['countdown'], 300)


# ---------------------------------------------------------------------------
# 3. Template rendering
# ---------------------------------------------------------------------------

class TestEmailTemplateRenderer(TestCase):

    def test_render_raw_with_variables(self):
        from apps.communications.email_dispatch.renderer import EmailTemplateRenderer
        renderer = EmailTemplateRenderer()
        result = renderer.render_raw(
            subject='Hello {name}',
            html='<p>Dear {name}, your interview is at {time}.</p>',
            context={'name': 'Alice', 'time': '10:00 AM'},
        )
        self.assertEqual(result.subject, 'Hello Alice')
        self.assertIn('Alice', result.html_body)
        self.assertIn('10:00 AM', result.html_body)

    def test_render_raw_missing_variable_renders_empty(self):
        from apps.communications.email_dispatch.renderer import EmailTemplateRenderer
        renderer = EmailTemplateRenderer()
        result = renderer.render_raw(
            subject='Hello {missing_var}',
            html='<p>Job: {job_title}</p>',
            context={},
        )
        # Missing variables render as empty string — no KeyError
        self.assertEqual(result.subject, 'Hello ')
        self.assertIn('Job: ', result.html_body)
        self.assertNotIn('{job_title}', result.html_body)

    def test_render_raw_generates_text_from_html_when_text_absent(self):
        from apps.communications.email_dispatch.renderer import EmailTemplateRenderer
        renderer = EmailTemplateRenderer()
        result = renderer.render_raw(
            subject='Test',
            html='<p>Hello <strong>World</strong></p>',
            context={},
        )
        # text_body should be derived by stripping HTML
        self.assertIn('Hello', result.text_body)
        self.assertNotIn('<p>', result.text_body)

    def test_render_raw_sanitizes_html_context_values(self):
        from apps.communications.email_dispatch.renderer import EmailTemplateRenderer
        renderer = EmailTemplateRenderer()
        result = renderer.render_raw(
            subject='Test',
            html='<p>Name: {name}</p>',
            context={'name': '<script>alert("xss")</script>'},
        )
        self.assertNotIn('<script>', result.html_body)
        self.assertIn('&lt;script&gt;', result.html_body)

    def test_render_raw_subject_not_html_escaped(self):
        """Subject is plain text — context values should NOT be HTML-escaped."""
        from apps.communications.email_dispatch.renderer import EmailTemplateRenderer
        renderer = EmailTemplateRenderer()
        result = renderer.render_raw(
            subject='Hello {name}',
            html='',
            context={'name': 'Alice & Bob'},
        )
        # Subject should contain literal & not &amp;
        self.assertEqual(result.subject, 'Hello Alice & Bob')

    def test_render_fallback_when_no_template_found(self):
        from apps.communications.email_dispatch.renderer import EmailTemplateRenderer
        renderer = EmailTemplateRenderer()
        # 'nonexistent_slug' won't be in DB → should return graceful fallback
        result = renderer.render(
            template_slug='nonexistent.slug',
            context={'subject': 'Fallback subject'},
        )
        self.assertIsInstance(result.subject, str)
        self.assertIsNotNone(result.text_body)


# ---------------------------------------------------------------------------
# 4. Tenant config switching
# ---------------------------------------------------------------------------

class TestTenantConfigSwitching(TestCase):

    def test_smtp_config_resolves_smtp_provider(self):
        from apps.communications.email_dispatch.providers import get_provider
        from apps.communications.email_dispatch.providers.smtp import SMTPAutomationProvider
        config = _make_tenant_config(provider='smtp')
        provider = get_provider(config)
        self.assertIsInstance(provider, SMTPAutomationProvider)
        self.assertEqual(provider.key, 'smtp')

    def test_sendgrid_config_resolves_sendgrid_provider(self):
        from apps.communications.email_dispatch.providers import get_provider
        from apps.communications.email_dispatch.providers.sendgrid import SendGridProvider
        config = _make_tenant_config(provider='sendgrid')
        provider = get_provider(config)
        self.assertIsInstance(provider, SendGridProvider)
        self.assertEqual(provider.key, 'sendgrid')

    def test_ses_config_resolves_ses_provider(self):
        from apps.communications.email_dispatch.providers import get_provider
        from apps.communications.email_dispatch.providers.ses import SESProvider
        config = _make_tenant_config(provider='ses')
        provider = get_provider(config)
        self.assertIsInstance(provider, SESProvider)
        self.assertEqual(provider.key, 'ses')

    def test_none_config_resolves_smtp_system_provider(self):
        from apps.communications.email_dispatch.providers import get_provider
        from apps.communications.email_dispatch.providers.smtp import SMTPAutomationProvider
        provider = get_provider(None)
        self.assertIsInstance(provider, SMTPAutomationProvider)
        self.assertIsNone(provider.config)

    @patch('apps.communications.email_dispatch.tasks.deliver_email_task.apply_async')
    def test_send_email_uses_tenant_provider(self, _mock):
        from apps.communications.email_delivery_models import TenantEmailConfig
        from apps.communications.email_delivery_service import EmailDeliveryService

        # TENANT_B has sendgrid config
        _make_tenant_config(tenant_id=TENANT_B, provider='sendgrid')
        delivery = EmailDeliveryService.send_email(
            tenant_id=str(TENANT_B),
            recipients=['x@example.com'],
            subject='Test',
            text_body='Hi',
        )
        self.assertEqual(delivery.provider, 'sendgrid')


# ---------------------------------------------------------------------------
# 5. Fallback email flow (send_email_for_notification)
# ---------------------------------------------------------------------------

class TestSendEmailForNotification(TestCase):

    def _make_notification(self, is_read=False):
        from apps.communications.models import Notification, NotificationSeverity
        return Notification.objects.create(
            user_id=USER_1,
            tenant_id=TENANT_A,
            title='Test notif',
            body='You have a pending action.',
            type='test.event',
            notification_type='test.event',
            severity=NotificationSeverity.HIGH,
            is_read=is_read,
        )

    @patch('apps.communications.email_dispatch.tasks.deliver_email_task.apply_async')
    @patch('apps.communications.email_delivery_service.EmailDeliveryService._resolve_user_email', return_value='user@example.com')
    def test_sends_email_for_unread_notification(self, _mock_email, mock_apply):
        from apps.communications.email_delivery_service import EmailDeliveryService
        notification = self._make_notification()
        delivery = EmailDeliveryService.send_email_for_notification(str(notification.id))
        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.recipient_email, 'user@example.com')
        self.assertIsNotNone(delivery.notification_id)
        mock_apply.assert_called_once()

    @patch('apps.communications.email_delivery_service.EmailDeliveryService._resolve_user_email', return_value='')
    def test_returns_none_when_user_has_no_email(self, _mock):
        from apps.communications.email_delivery_service import EmailDeliveryService
        notification = self._make_notification()
        delivery = EmailDeliveryService.send_email_for_notification(str(notification.id))
        self.assertIsNone(delivery)

    def test_returns_none_for_nonexistent_notification(self):
        from apps.communications.email_delivery_service import EmailDeliveryService
        delivery = EmailDeliveryService.send_email_for_notification(str(uuid.uuid4()))
        self.assertIsNone(delivery)

    @patch('apps.communications.email_dispatch.tasks.deliver_email_task.apply_async')
    @patch('apps.communications.email_delivery_service.EmailDeliveryService._resolve_user_email', return_value='u@x.com')
    def test_critical_notification_uses_urgent_priority(self, _mock_email, _mock_apply):
        from apps.communications.email_delivery_service import EmailDeliveryService
        from apps.communications.models import Notification, NotificationSeverity
        notification = Notification.objects.create(
            user_id=USER_1,
            tenant_id=TENANT_A,
            title='Critical',
            body='Critical alert',
            type='test.critical',
            notification_type='test.critical',
            severity=NotificationSeverity.CRITICAL,
            is_read=False,
        )
        delivery = EmailDeliveryService.send_email_for_notification(str(notification.id))
        self.assertEqual(delivery.priority, 'urgent')


# ---------------------------------------------------------------------------
# 6. Retry stop condition
# ---------------------------------------------------------------------------

class TestRetryStopCondition(TestCase):

    def test_schedule_retry_marks_failed_when_max_retries_exhausted(self):
        delivery = _make_delivery(retry_count=4, max_retries=4, status='failed')
        from apps.communications.email_delivery_service import EmailDeliveryService
        result = EmailDeliveryService.schedule_retry(
            delivery_id=str(delivery.id),
            current_retry_count=4,
        )
        self.assertFalse(result)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, 'failed')

    def test_can_retry_returns_false_when_sent(self):
        delivery = _make_delivery(status='sent')
        self.assertFalse(delivery.can_retry())

    def test_can_retry_returns_true_for_failed_within_limit(self):
        delivery = _make_delivery(status='failed', retry_count=1, max_retries=4)
        self.assertTrue(delivery.can_retry())

    def test_deliver_task_does_not_reprocess_sent_delivery(self):
        delivery = _make_delivery(status='sent')
        with patch(
            'apps.communications.email_dispatch.providers.smtp.SMTPAutomationProvider.send',
        ) as mock_send:
            from apps.communications.email_dispatch.tasks import deliver_email_task
            deliver_email_task(str(delivery.id))
        mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# 7. Multi-tenant isolation
# ---------------------------------------------------------------------------

class TestMultiTenantIsolation(TestCase):

    def test_delivery_list_view_scoped_to_tenant(self):
        from apps.communications.email_dispatch.views import EmailDeliveryListView

        # Create deliveries for two tenants
        _make_delivery(tenant_id=TENANT_A)
        _make_delivery(tenant_id=TENANT_B)

        factory = APIRequestFactory()
        request = factory.get('/communications/email/deliveries/')
        request.user = _make_user(tenant_id=TENANT_A)
        force_authenticate(request, user=request.user)
        view = EmailDeliveryListView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        for item in response.data['results']:
            self.assertEqual(str(item['tenant_id']), str(TENANT_A))

    def test_delivery_detail_view_denies_cross_tenant_access(self):
        from apps.communications.email_dispatch.views import EmailDeliveryDetailView
        delivery_b = _make_delivery(tenant_id=TENANT_B)

        factory = APIRequestFactory()
        request = factory.get(f'/communications/email/deliveries/{delivery_b.id}/')
        request.user = _make_user(tenant_id=TENANT_A)
        force_authenticate(request, user=request.user)
        view = EmailDeliveryDetailView.as_view()
        response = view(request, delivery_id=str(delivery_b.id))

        self.assertEqual(response.status_code, 404)

    @patch('apps.communications.email_dispatch.tasks.deliver_email_task.apply_async')
    def test_send_email_records_correct_tenant_id(self, _mock):
        from apps.communications.email_delivery_service import EmailDeliveryService
        delivery = EmailDeliveryService.send_email(
            tenant_id=str(TENANT_B),
            recipients=['z@example.com'],
            subject='TenantB email',
            text_body='Hi',
        )
        self.assertEqual(str(delivery.tenant_id), str(TENANT_B))


# ---------------------------------------------------------------------------
# 8. Priority queue routing
# ---------------------------------------------------------------------------

class TestPriorityQueueRouting(TestCase):

    @patch('apps.communications.email_dispatch.tasks.deliver_email_task.apply_async')
    def test_urgent_priority_routes_to_email_high_queue(self, mock_apply):
        from apps.communications.email_delivery_service import EmailDeliveryService
        EmailDeliveryService.send_email(
            tenant_id=str(TENANT_A),
            recipients=['u@x.com'],
            subject='Urgent',
            text_body='Hi',
            priority='urgent',
        )
        call_kwargs = mock_apply.call_args.kwargs
        self.assertEqual(call_kwargs['queue'], 'email_high')

    @patch('apps.communications.email_dispatch.tasks.deliver_email_task.apply_async')
    def test_normal_priority_routes_to_email_normal_queue(self, mock_apply):
        from apps.communications.email_delivery_service import EmailDeliveryService
        EmailDeliveryService.send_email(
            tenant_id=str(TENANT_A),
            recipients=['u@x.com'],
            subject='Normal',
            text_body='Hi',
            priority='normal',
        )
        call_kwargs = mock_apply.call_args.kwargs
        self.assertEqual(call_kwargs['queue'], 'email_normal')

    @patch('apps.communications.email_dispatch.tasks.deliver_email_task.apply_async')
    def test_low_priority_routes_to_email_low_queue(self, mock_apply):
        from apps.communications.email_delivery_service import EmailDeliveryService
        EmailDeliveryService.send_email(
            tenant_id=str(TENANT_A),
            recipients=['u@x.com'],
            subject='Low',
            text_body='Hi',
            priority='low',
        )
        call_kwargs = mock_apply.call_args.kwargs
        self.assertEqual(call_kwargs['queue'], 'email_low')


# ---------------------------------------------------------------------------
# 9. Provider health_check / validate_config
# ---------------------------------------------------------------------------

class TestProviderValidation(TestCase):

    def test_smtp_validate_config_ok_with_valid_fields(self):
        config = _make_tenant_config(provider='smtp', smtp_host='smtp.example.com')
        from apps.communications.email_dispatch.providers.smtp import SMTPAutomationProvider
        provider = SMTPAutomationProvider(config=config)
        valid, error = provider.validate_config()
        self.assertTrue(valid)
        self.assertEqual(error, '')

    def test_smtp_validate_config_fails_without_host(self):
        config = _make_tenant_config(provider='smtp')
        config.smtp_host = ''
        from apps.communications.email_dispatch.providers.smtp import SMTPAutomationProvider
        provider = SMTPAutomationProvider(config=config)
        valid, error = provider.validate_config()
        self.assertFalse(valid)
        self.assertIn('smtp_host', error)

    def test_sendgrid_validate_config_fails_without_api_key(self):
        config = _make_tenant_config(provider='sendgrid')
        config.sendgrid_api_key_encrypted = ''
        from apps.communications.email_dispatch.providers.sendgrid import SendGridProvider
        provider = SendGridProvider(config=config)
        valid, error = provider.validate_config()
        self.assertFalse(valid)
        self.assertIn('api_key', error.lower())

    def test_ses_validate_config_fails_without_region(self):
        config = _make_tenant_config(provider='ses')
        config.ses_region = ''
        from apps.communications.email_dispatch.providers.ses import SESProvider
        provider = SESProvider(config=config)
        valid, error = provider.validate_config()
        self.assertFalse(valid)

    def test_smtp_health_check_returns_dict_with_status(self):
        from apps.communications.email_dispatch.providers.smtp import SMTPAutomationProvider
        with patch.object(
            SMTPAutomationProvider, '_get_connection',
            side_effect=Exception('connection refused'),
        ):
            provider = SMTPAutomationProvider(config=None)
            result = provider.health_check()
        self.assertIn('status', result)
        self.assertEqual(result['provider'], 'smtp')
        self.assertEqual(result['status'], 'unhealthy')

    def test_sendgrid_health_check_unhealthy_without_api_key(self):
        config = _make_tenant_config(provider='sendgrid')
        config.sendgrid_api_key_encrypted = ''
        from apps.communications.email_dispatch.providers.sendgrid import SendGridProvider
        provider = SendGridProvider(config=config)
        result = provider.health_check()
        self.assertEqual(result['status'], 'unhealthy')


# ---------------------------------------------------------------------------
# 10. EmailDelivery state transitions
# ---------------------------------------------------------------------------

class TestEmailDeliveryStateTransitions(TestCase):

    def test_mark_sent_updates_status_and_timestamp(self):
        delivery = _make_delivery()
        delivery.mark_sent(provider_message_id='abc123')
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, 'sent')
        self.assertIsNotNone(delivery.sent_at)
        self.assertEqual(delivery.provider_message_id, 'abc123')
        self.assertEqual(delivery.error_message, '')

    def test_mark_failed_stores_error(self):
        delivery = _make_delivery()
        delivery.mark_failed(error='SMTP timeout')
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, 'failed')
        self.assertIn('SMTP timeout', delivery.error_message)

    def test_mark_deferred_increments_retry_count(self):
        from django.utils import timezone
        delivery = _make_delivery(retry_count=0)
        next_at = timezone.now() + timezone.timedelta(minutes=1)
        delivery.mark_deferred(next_retry_at=next_at, error='transient error')
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, 'deferred')
        self.assertEqual(delivery.retry_count, 1)
        self.assertIsNotNone(delivery.next_retry_at)

    def test_mark_delivered_sets_timestamp(self):
        delivery = _make_delivery(status='sent')
        delivery.mark_delivered()
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, 'delivered')
        self.assertIsNotNone(delivery.delivered_at)

    def test_error_message_truncated_at_2000_chars(self):
        delivery = _make_delivery()
        long_error = 'x' * 3000
        delivery.mark_failed(error=long_error)
        delivery.refresh_from_db()
        self.assertLessEqual(len(delivery.error_message), 2000)


# ---------------------------------------------------------------------------
# 11. Sender resolution
# ---------------------------------------------------------------------------

class TestSenderResolution(TestCase):

    def test_resolves_from_config_when_present(self):
        config = _make_tenant_config(from_email='ops@company.com', from_name='OpsBot')
        from apps.communications.email_delivery_service import EmailDeliveryService
        from_email, from_name = EmailDeliveryService._resolve_sender(config)
        self.assertEqual(from_email, 'ops@company.com')
        self.assertEqual(from_name, 'OpsBot')

    def test_falls_back_to_settings_when_no_config(self):
        from apps.communications.email_delivery_service import EmailDeliveryService
        from_email, from_name = EmailDeliveryService._resolve_sender(None)
        self.assertIn('@', from_email)  # is a valid email

    def test_config_from_email_overrides_settings(self):
        config = _make_tenant_config(from_email='custom@domain.com', from_name='Custom')
        from apps.communications.email_delivery_service import EmailDeliveryService
        from_email, _ = EmailDeliveryService._resolve_sender(config)
        self.assertEqual(from_email, 'custom@domain.com')


# ---------------------------------------------------------------------------
# 12. Renderer HTML safety
# ---------------------------------------------------------------------------

class TestRendererHTMLSafety(TestCase):

    def test_html_injection_via_context_is_escaped(self):
        from apps.communications.email_dispatch.renderer import EmailTemplateRenderer
        renderer = EmailTemplateRenderer()
        result = renderer.render_raw(
            subject='Test',
            html='<p>{body}</p>',
            context={'body': '<img src=x onerror=alert(1)>'},
        )
        # Raw <img> tag must not appear — it must be HTML-entity-escaped
        self.assertNotIn('<img', result.html_body)
        # The escaped form &lt;img ... &gt; should be present (safe to render)
        self.assertIn('&lt;img', result.html_body)

    def test_none_context_value_renders_empty_string(self):
        from apps.communications.email_dispatch.renderer import EmailTemplateRenderer
        renderer = EmailTemplateRenderer()
        result = renderer.render_raw(
            subject='{greeting}',
            html='<p>{greeting}</p>',
            context={'greeting': None},
        )
        self.assertEqual(result.subject, '')
        self.assertNotIn('{greeting}', result.html_body)


# ---------------------------------------------------------------------------
# 13. Observability API endpoints
# ---------------------------------------------------------------------------

class TestObservabilityEndpoints(TestCase):

    def test_delivery_list_requires_auth(self):
        from apps.communications.email_dispatch.views import EmailDeliveryListView
        from unittest.mock import MagicMock
        factory = APIRequestFactory()
        request = factory.get('/communications/email/deliveries/')
        # Unauthenticated
        anon = MagicMock()
        anon.is_authenticated = False
        anon.role = 'viewer'
        anon.tenant_id = TENANT_A
        request.user = anon
        force_authenticate(request, user=anon)
        view = EmailDeliveryListView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_delivery_list_admin_returns_200(self):
        from apps.communications.email_dispatch.views import EmailDeliveryListView
        _make_delivery(tenant_id=TENANT_A)
        factory = APIRequestFactory()
        request = factory.get('/communications/email/deliveries/')
        request.user = _make_user(tenant_id=TENANT_A, role='tenant_admin')
        force_authenticate(request, user=request.user)
        response = EmailDeliveryListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)

    def test_delivery_list_filters_by_status(self):
        from apps.communications.email_dispatch.views import EmailDeliveryListView
        _make_delivery(tenant_id=TENANT_A, status='sent')
        _make_delivery(tenant_id=TENANT_A, status='failed')
        factory = APIRequestFactory()
        request = factory.get('/communications/email/deliveries/?status=sent')
        request.user = _make_user(role='tenant_admin')
        force_authenticate(request, user=request.user)
        response = EmailDeliveryListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        for item in response.data['results']:
            self.assertEqual(item['status'], 'sent')

    def test_delivery_detail_returns_correct_record(self):
        from apps.communications.email_dispatch.views import EmailDeliveryDetailView
        delivery = _make_delivery(tenant_id=TENANT_A)
        factory = APIRequestFactory()
        request = factory.get(f'/communications/email/deliveries/{delivery.id}/')
        request.user = _make_user(role='tenant_admin')
        force_authenticate(request, user=request.user)
        response = EmailDeliveryDetailView.as_view()(request, delivery_id=str(delivery.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.data['id']), str(delivery.id))

    def test_delivery_retry_view_requeues_failed_delivery(self):
        from apps.communications.email_dispatch.views import EmailDeliveryRetryView
        delivery = _make_delivery(tenant_id=TENANT_A, status='failed')
        with patch(
            'apps.communications.email_dispatch.tasks.deliver_email_task.apply_async',
        ) as mock_apply:
            factory = APIRequestFactory()
            request = factory.post(f'/communications/email/deliveries/{delivery.id}/retry/')
            request.user = _make_user(role='tenant_admin')
            force_authenticate(request, user=request.user)
            response = EmailDeliveryRetryView.as_view()(request, delivery_id=str(delivery.id))
        self.assertEqual(response.status_code, 202)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, 'pending')
        self.assertEqual(delivery.retry_count, 0)
        mock_apply.assert_called_once()

    def test_health_view_returns_overall_status(self):
        from apps.communications.email_dispatch.views import EmailHealthView
        from apps.communications.email_dispatch.providers.base import ProviderHealthStatus
        healthy_result = {
            'status': ProviderHealthStatus.HEALTHY,
            'provider': 'smtp',
            'detail': 'OK',
            'latency_ms': 5,
        }
        with patch(
            'apps.communications.email_dispatch.providers.smtp.SMTPAutomationProvider.health_check',
            return_value=healthy_result,
        ):
            factory = APIRequestFactory()
            request = factory.get('/communications/email/health/')
            request.user = _make_user(role='tenant_admin')
            force_authenticate(request, user=request.user)
            response = EmailHealthView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('overall', response.data)
        self.assertIn('checks', response.data)
