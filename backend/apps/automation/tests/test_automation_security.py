import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.automation.models import AutomationRule
from apps.automation.views import (
    AutomationRuleListView,
    AutomationRuleDetailView,
    AutonomousActionUpdateView,
    AutomationTriggerView,
)


class AutomationSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate = CustomUser.objects.create_user(
            email='automation-candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )
        self.recruiter = CustomUser.objects.create_user(
            email='automation-recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )
        self.tenant_admin = CustomUser.objects.create_user(
            email='automation-tenant-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_id,
        )
        self.permission_patch = patch('apps.rbac.permissions.user_has_all_permissions', return_value=True)
        self.permission_patch.start()
        self.addCleanup(self.permission_patch.stop)

    def _rule_payload(self):
        return {
            'name': 'Security Rule',
            'description': 'Rule for security tests',
            'trigger_event': 'candidate.applied',
            'conditions': {'all': [{'field': 'match_score', 'operator': 'gte', 'value': 80}]},
            'actions': [{'type': 'shortlist_candidate'}],
            'is_active': True,
        }

    def test_candidate_cannot_create_rule(self):
        request = self.factory.post('/api/v1/automation/rules/', self._rule_payload(), format='json')
        force_authenticate(request, user=self.candidate)
        response = AutomationRuleListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_recruiter_cannot_create_rule(self):
        request = self.factory.post('/api/v1/automation/rules/', self._rule_payload(), format='json')
        force_authenticate(request, user=self.recruiter)
        response = AutomationRuleListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_tenant_admin_can_create_rule(self):
        request = self.factory.post('/api/v1/automation/rules/', self._rule_payload(), format='json')
        force_authenticate(request, user=self.tenant_admin)
        response = AutomationRuleListView.as_view()(request)
        self.assertEqual(response.status_code, 201)

    def test_recruiter_cannot_update_or_delete_rule(self):
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.tenant_admin.id,
            name='Existing Rule',
            trigger_event='candidate.applied',
            conditions={},
            actions=[{'type': 'send_notification'}],
        )
        update_request = self.factory.put(
            f'/api/v1/automation/rules/{rule.id}/',
            {'name': 'Updated by recruiter'},
            format='json',
        )
        force_authenticate(update_request, user=self.recruiter)
        update_response = AutomationRuleDetailView.as_view()(update_request, pk=rule.id)
        self.assertEqual(update_response.status_code, 403)

        delete_request = self.factory.delete(f'/api/v1/automation/rules/{rule.id}/')
        force_authenticate(delete_request, user=self.recruiter)
        delete_response = AutomationRuleDetailView.as_view()(delete_request, pk=rule.id)
        self.assertEqual(delete_response.status_code, 403)

    def test_candidate_cannot_run_automation_actions_or_triggers(self):
        action_request = self.factory.post(
            '/api/v1/automation/autonomous/00000000-0000-0000-0000-000000000001/action/',
            {'action': 'approve', 'item_type': 'suggestion'},
            format='json',
        )
        force_authenticate(action_request, user=self.candidate)
        action_response = AutonomousActionUpdateView.as_view()(
            action_request,
            pk='00000000-0000-0000-0000-000000000001',
        )
        self.assertEqual(action_response.status_code, 403)

        trigger_request = self.factory.post(
            '/api/v1/automation/trigger/',
            {'trigger_event': 'candidate.applied'},
            format='json',
        )
        force_authenticate(trigger_request, user=self.candidate)
        trigger_response = AutomationTriggerView.as_view()(trigger_request)
        self.assertEqual(trigger_response.status_code, 403)

    def test_recruiter_can_reach_autonomous_action_guarded_logic(self):
        request = self.factory.post(
            '/api/v1/automation/autonomous/00000000-0000-0000-0000-000000000001/action/',
            {'action': 'invalid', 'item_type': 'suggestion'},
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        response = AutonomousActionUpdateView.as_view()(
            request,
            pk='00000000-0000-0000-0000-000000000001',
        )
        self.assertNotEqual(response.status_code, 403)
