from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.automation.models import AutomationRule, AutomationLog
from apps.automation.services import AutomationEngine
from apps.automation.views import AutomationRuleListView
from apps.core import events
from apps.pipeline.models import Application


class InterviewAutomationEngineTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create_user(
            email='automation-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id='00000000-0000-0000-0000-000000000001',
        )
        self.permission_patch = patch('apps.rbac.permissions.user_has_all_permissions', return_value=True)
        self.permission_patch.start()
        self.addCleanup(self.permission_patch.stop)

    def test_rule_create_works(self):
        request = self.factory.post(
            '/api/v1/automation/rules/',
            {
                'name': 'Auto shortlist high score',
                'description': 'Shortlist if score is strong',
                'trigger_event': 'candidate.applied',
                'conditions': {'all': [{'field': 'match_score', 'operator': 'gte', 'value': 80}]},
                'actions': [{'type': 'shortlist_candidate'}],
                'is_active': True,
            },
            format='json',
        )
        force_authenticate(request, user=self.user)
        response = AutomationRuleListView.as_view()(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(AutomationRule.objects.filter(tenant_id=self.user.tenant_id, is_deleted=False).count(), 1)

    def test_trigger_fires(self):
        rule = AutomationRule.objects.create(
            tenant_id=self.user.tenant_id,
            created_by=self.user.id,
            name='Log candidate apply',
            trigger_event='candidate.applied',
            conditions={},
            actions=[{'type': 'send_notification', 'channel': 'in_app'}],
        )
        app = Application.objects.create(
            tenant_id=self.user.tenant_id,
            candidate_id='00000000-0000-0000-0000-000000000111',
            requisition_id='00000000-0000-0000-0000-000000000222',
            status='applied',
        )
        events.application.created.send(sender=self.__class__, application=app)
        self.assertTrue(AutomationLog.objects.filter(rule_id=rule.id, trigger_event='candidate.applied').exists())

    def test_action_executes(self):
        AutomationRule.objects.create(
            tenant_id=self.user.tenant_id,
            created_by=self.user.id,
            name='Auto shortlist',
            trigger_event='candidate.applied',
            conditions={'all': [{'field': 'match_score', 'operator': 'gte', 'value': 70}]},
            actions=[{'type': 'shortlist_candidate'}],
        )
        app = Application.objects.create(
            tenant_id=self.user.tenant_id,
            candidate_id='00000000-0000-0000-0000-000000000333',
            requisition_id='00000000-0000-0000-0000-000000000444',
            status='applied',
            match_score=85,
        )
        AutomationEngine.execute_trigger(
            trigger_event='candidate.applied',
            tenant_id=self.user.tenant_id,
            context={
                'application_id': str(app.id),
                'candidate_id': str(app.candidate_id),
                'requisition_id': str(app.requisition_id),
                'match_score': float(app.match_score),
            },
            actor_user_id=self.user.id,
            entity_type='application',
            entity_id=app.id,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, 'shortlisted')

