"""
QA Tests: Notification Control Center
Tests for NotificationControlService, model creation, and API views.
Uses APIRequestFactory + force_authenticate + real CustomUser (project convention).
"""
import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.communications.notification_control_models import (
    NotificationRule, NotificationChannelSetting,
    TenantNotificationPreferenceDefaults,
)
from apps.communications.notification_control_service import NotificationControlService
from apps.communications.notification_control_views import (
    NotificationRuleListView,
    NotificationRuleDetailView,
    NotificationChannelSettingsView,
    NotificationPreferenceDefaultsView,
    NotificationControlSummaryView,
)

TENANT_A = uuid.UUID('00000000-0000-0000-0000-000000000010')
TENANT_B = uuid.UUID('00000000-0000-0000-0000-000000000011')


def _admin(email, tenant_id=TENANT_A):
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return CustomUser.objects.create_user(
            email=email, password='testpass', role='tenant_admin', tenant_id=tenant_id,
        )


# ---------------------------------------------------------------------------
# NotificationControlService Tests (pure service, no HTTP)
# ---------------------------------------------------------------------------

class TestNotificationControlServiceDefaults(TestCase):

    def test_ensure_defaults_seeded(self):
        NotificationControlService._ensure_defaults_seeded(tenant_id=TENANT_A)
        count = NotificationRule.objects.filter(tenant_id=None, is_system=True).count()
        self.assertGreater(count, 0)

    def test_idempotent_seeding(self):
        NotificationControlService._ensure_defaults_seeded(tenant_id=TENANT_A)
        before = NotificationRule.objects.filter(tenant_id=None, is_system=True).count()
        NotificationControlService._ensure_defaults_seeded(tenant_id=TENANT_B)
        after = NotificationRule.objects.filter(tenant_id=None, is_system=True).count()
        self.assertEqual(before, after)


class TestNotificationControlServiceGetRule(TestCase):

    def setUp(self):
        NotificationControlService._ensure_defaults_seeded(tenant_id=TENANT_A)

    def test_get_system_rule(self):
        rule = NotificationControlService.get_rule(
            tenant_id=TENANT_A, event_key='application_submitted',
        )
        self.assertIsNotNone(rule)
        self.assertEqual(rule.event_key, 'application_submitted')

    def test_tenant_override_takes_precedence(self):
        NotificationControlService.upsert_rule(
            tenant_id=TENANT_A,
            event_key='application_submitted',
            business_label='My Custom Label',
            priority='critical',
        )
        rule = NotificationControlService.get_rule(
            tenant_id=TENANT_A, event_key='application_submitted',
        )
        self.assertEqual(rule.tenant_id, TENANT_A)
        self.assertEqual(rule.priority, 'critical')

    def test_tenant_b_not_affected_by_tenant_a_override(self):
        NotificationControlService.upsert_rule(
            tenant_id=TENANT_A,
            event_key='application_submitted',
            business_label='A Override',
            priority='critical',
        )
        rule = NotificationControlService.get_rule(
            tenant_id=TENANT_B, event_key='application_submitted',
        )
        self.assertIsNone(rule.tenant_id)

    def test_returns_none_for_unknown_event_key(self):
        rule = NotificationControlService.get_rule(
            tenant_id=TENANT_A, event_key='nonexistent_event_xyz',
        )
        self.assertIsNone(rule)


class TestNotificationControlServiceListRules(TestCase):

    def test_list_rules_includes_system_defaults(self):
        rules = NotificationControlService.list_rules(tenant_id=TENANT_A)
        self.assertGreater(len(rules), 10)
        event_keys = [r.event_key for r in rules]
        self.assertIn('application_submitted', event_keys)
        self.assertIn('interview_scheduled', event_keys)
        self.assertIn('offer_sent', event_keys)

    def test_tenant_override_replaces_system_in_list(self):
        NotificationControlService.upsert_rule(
            tenant_id=TENANT_A,
            event_key='application_submitted',
            business_label='Overridden',
            priority='critical',
        )
        rules = NotificationControlService.list_rules(tenant_id=TENANT_A)
        submitted = next(r for r in rules if r.event_key == 'application_submitted')
        self.assertEqual(submitted.tenant_id, TENANT_A)
        self.assertEqual(submitted.priority, 'critical')
        count = sum(1 for r in rules if r.event_key == 'application_submitted')
        self.assertEqual(count, 1)


class TestNotificationControlServiceUpsertRule(TestCase):

    def test_upsert_creates_rule(self):
        rule = NotificationControlService.upsert_rule(
            tenant_id=TENANT_A,
            event_key='custom_event',
            business_label='Custom Event',
            category='system',
            priority='medium',
            fallback_enabled=True,
            fallback_delay_minutes=20,
        )
        self.assertEqual(rule.tenant_id, TENANT_A)
        self.assertEqual(rule.fallback_delay_minutes, 20)

    def test_upsert_updates_existing_rule(self):
        NotificationControlService.upsert_rule(
            tenant_id=TENANT_A,
            event_key='custom_event_2',
            business_label='Test',
        )
        updated = NotificationControlService.upsert_rule(
            tenant_id=TENANT_A,
            event_key='custom_event_2',
            business_label='Test Updated',
            priority='high',
        )
        self.assertEqual(updated.business_label, 'Test Updated')
        self.assertEqual(updated.priority, 'high')


class TestNotificationControlServiceDeleteRule(TestCase):

    def test_soft_delete_tenant_rule(self):
        rule = NotificationControlService.upsert_rule(
            tenant_id=TENANT_A,
            event_key='deletable_event',
            business_label='Deletable',
        )
        NotificationControlService.delete_rule(tenant_id=TENANT_A, rule_id=rule.id)
        rule.refresh_from_db()
        self.assertTrue(rule.is_deleted)

    def test_cannot_delete_system_rule(self):
        system_rule = NotificationRule.objects.create(
            tenant_id=None,
            event_key='system_only_event',
            business_label='System Rule',
            is_system=True,
        )
        with self.assertRaises(ValueError):
            NotificationControlService.delete_rule(
                tenant_id=TENANT_A, rule_id=system_rule.id,
            )


class TestChannelSettings(TestCase):

    def test_get_channel_settings_creates_defaults(self):
        settings = NotificationControlService.get_channel_settings(tenant_id=TENANT_A)
        channel_types = [s.channel_type for s in settings]
        self.assertIn('in_app', channel_types)
        self.assertIn('email', channel_types)

    def test_update_channel_settings(self):
        NotificationControlService.get_channel_settings(tenant_id=TENANT_A)
        updated = NotificationControlService.update_channel_settings(
            tenant_id=TENANT_A,
            settings=[
                {'channel_type': 'email',   'is_enabled': False},
                {'channel_type': 'in_app',  'is_enabled': True},
            ],
        )
        email_setting = next(s for s in updated if s.channel_type == 'email')
        self.assertFalse(email_setting.is_enabled)

    def test_channel_enabled_returns_false_when_disabled(self):
        NotificationControlService.update_channel_settings(
            tenant_id=TENANT_A,
            settings=[{'channel_type': 'whatsapp', 'is_enabled': False}],
        )
        enabled = NotificationControlService.channel_enabled(tenant_id=TENANT_A, channel='whatsapp')
        self.assertFalse(enabled)

    def test_channel_enabled_defaults_true_when_no_setting(self):
        enabled = NotificationControlService.channel_enabled(
            tenant_id=uuid.uuid4(), channel='email',
        )
        self.assertTrue(enabled)


class TestPreferenceDefaults(TestCase):

    def test_get_creates_defaults(self):
        prefs = NotificationControlService.get_preference_defaults(tenant_id=TENANT_A)
        self.assertTrue(prefs.default_in_app_enabled)
        self.assertTrue(prefs.allow_user_override)

    def test_update_preferences(self):
        NotificationControlService.update_preference_defaults(
            tenant_id=TENANT_A,
            default_email_enabled=False,
            allow_user_override=False,
        )
        prefs = NotificationControlService.get_preference_defaults(tenant_id=TENANT_A)
        self.assertFalse(prefs.default_email_enabled)
        self.assertFalse(prefs.allow_user_override)


class TestNotificationControlSummary(TestCase):

    def test_summary_structure(self):
        summary = NotificationControlService.get_summary(tenant_id=TENANT_A)
        self.assertIn('total_rules', summary)
        self.assertIn('active_rules', summary)
        self.assertIn('fallback_enabled_count', summary)
        self.assertIn('escalation_enabled_count', summary)
        self.assertIn('high_priority_count', summary)
        self.assertIn('email_channel_enabled', summary)
        self.assertIn('in_app_channel_enabled', summary)
        self.assertGreater(summary['total_rules'], 0)


# ---------------------------------------------------------------------------
# API View Tests
# ---------------------------------------------------------------------------

factory = APIRequestFactory()

# RBAC setup helper — seeds the Role + Permissions needed for notification
# control views so tests can use real users without bypassing security.

def _seed_nc_permissions(user):
    """Grant notification_rules.view + manage permissions to user's role."""
    from apps.rbac.models import Role, Permission
    from django.core.cache import cache

    view_perm, _ = Permission.objects.get_or_create(
        code='communication.notification_rules.view',
        defaults={'label': 'View notification rules', 'module': 'communication',
                  'resource': 'notification_rules', 'action': 'view', 'is_active': True},
    )
    manage_perm, _ = Permission.objects.get_or_create(
        code='communication.notification_rules.manage',
        defaults={'label': 'Manage notification rules', 'module': 'communication',
                  'resource': 'notification_rules', 'action': 'manage', 'is_active': True},
    )
    role, _ = Role.objects.get_or_create(
        name=user.role,
        tenant_id=user.tenant_id,
        defaults={'display_name': 'Tenant Admin', 'is_system': False},
    )
    role.permissions.add(view_perm, manage_perm)
    cache.clear()  # bust RBAC cache so new permissions are seen immediately


class _NCAPITestBase(TestCase):
    """Base for all view tests: seeds RBAC permissions once."""

    def setUp(self):
        self.user = _admin(self._email, TENANT_A)
        _seed_nc_permissions(self.user)


class TestNotificationRuleListAPI(_NCAPITestBase):
    _email = 'nc_rule_list@test.com'

    def test_get_returns_rules(self):
        request = factory.get('/notification-control/rules/')
        force_authenticate(request, user=self.user)
        response = NotificationRuleListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('rules', response.data['data'])
        self.assertGreater(len(response.data['data']['rules']), 0)

    def test_post_creates_rule(self):
        request = factory.post('/notification-control/rules/', {
            'event_key': 'test_api_event',
            'business_label': 'Test API Event',
            'category': 'system',
            'priority': 'medium',
            'fallback_enabled': True,
            'fallback_delay_minutes': 30,
        }, format='json')
        force_authenticate(request, user=self.user)
        response = NotificationRuleListView.as_view()(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['rule']['event_key'], 'test_api_event')


class TestNotificationRuleDetailAPI(_NCAPITestBase):
    _email = 'nc_rule_detail@test.com'

    def setUp(self):
        super().setUp()
        NotificationControlService._ensure_defaults_seeded(tenant_id=TENANT_A)

    def test_get_existing_rule(self):
        request = factory.get('/notification-control/rules/application_submitted/')
        force_authenticate(request, user=self.user)
        response = NotificationRuleDetailView.as_view()(request, event_key='application_submitted')
        self.assertEqual(response.status_code, 200)

    def test_get_nonexistent_rule_returns_404(self):
        request = factory.get('/notification-control/rules/nonexistent/')
        force_authenticate(request, user=self.user)
        response = NotificationRuleDetailView.as_view()(request, event_key='nonexistent')
        self.assertEqual(response.status_code, 404)

    def test_put_updates_rule(self):
        request = factory.put(
            '/notification-control/rules/application_submitted/',
            {'fallback_delay_minutes': 15, 'escalation_enabled': True},
            format='json',
        )
        force_authenticate(request, user=self.user)
        response = NotificationRuleDetailView.as_view()(request, event_key='application_submitted')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['rule']['fallback_delay_minutes'], 15)


class TestChannelSettingsAPI(_NCAPITestBase):
    _email = 'nc_channel@test.com'

    def test_get_channel_settings(self):
        request = factory.get('/notification-control/channel-settings/')
        force_authenticate(request, user=self.user)
        response = NotificationChannelSettingsView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('channel_settings', response.data['data'])

    def test_put_channel_settings(self):
        request = factory.put(
            '/notification-control/channel-settings/',
            {'settings': [{'channel_type': 'email', 'is_enabled': False}]},
            format='json',
        )
        force_authenticate(request, user=self.user)
        response = NotificationChannelSettingsView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        email = next(
            s for s in response.data['data']['channel_settings']
            if s['channel_type'] == 'email'
        )
        self.assertFalse(email['is_enabled'])


class TestPreferenceDefaultsAPI(_NCAPITestBase):
    _email = 'nc_prefs@test.com'

    def test_get_preferences(self):
        request = factory.get('/notification-control/default-preferences/')
        force_authenticate(request, user=self.user)
        response = NotificationPreferenceDefaultsView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('preferences', response.data['data'])

    def test_put_preferences(self):
        request = factory.put(
            '/notification-control/default-preferences/',
            {'default_email_enabled': False},
            format='json',
        )
        force_authenticate(request, user=self.user)
        response = NotificationPreferenceDefaultsView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['data']['preferences']['default_email_enabled'])


class TestSummaryAPI(_NCAPITestBase):
    _email = 'nc_summary@test.com'

    def test_get_summary(self):
        request = factory.get('/notification-control/summary/')
        force_authenticate(request, user=self.user)
        response = NotificationControlSummaryView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        summary = response.data['data']['summary']
        self.assertGreater(summary['total_rules'], 0)
        self.assertIn('email_channel_enabled', summary)
