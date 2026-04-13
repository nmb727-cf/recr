import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.orchestration_center.api.views import (
    AutomationIntelligencePolicyDetailView,
    AutomationIntelligencePolicyListCreateView,
)
from apps.orchestration_center.models import AISuggestion, AutomationIntelligencePolicy
from apps.orchestration_center.services.automation_intelligence_service import AutomationIntelligenceService
from apps.orchestration_center.services.suggestion_policy_evaluator import AutoApplyGuard
from apps.orchestration_center.services.suggestion_service import SuggestionService
from shared.owner_contracts import OwnerContractError


class AutomationIntelligenceTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.UUID('00000000-0000-0000-0000-000000000131')
        self.other_tenant_id = uuid.UUID('00000000-0000-0000-0000-000000000232')
        self.user = get_user_model().objects.create_user(
            email='tenant-admin-automation@example.com',
            password='password',
            tenant_id=self.tenant_id,
            role='tenant_admin',
            is_staff=True,
        )
        self.hr_manager = get_user_model().objects.create_user(
            email='hr-automation@example.com',
            password='password',
            tenant_id=self.tenant_id,
            role='hr_manager',
            is_staff=True,
        )
        self.other_tenant_user = get_user_model().objects.create_user(
            email='other-automation@example.com',
            password='password',
            tenant_id=self.other_tenant_id,
            role='tenant_admin',
            is_staff=True,
        )
        self.factory = APIRequestFactory()

    def _call_view(self, view, method, path, user, data=None, **kwargs):
        request_factory = getattr(self.factory, method.lower())
        request = request_factory(path, data=data, format='json')
        force_authenticate(request, user=user)
        response = view.as_view()(request, **kwargs)
        response.render()
        return response

    def _suggestion_payload(self, **overrides):
        payload = {
            'suggestion_key': 'candidate-followup',
            'category': 'followup_recommendation',
            'source_event': 'candidate.updated',
            'source_module': 'communications',
            'source_entity_type': 'candidate',
            'source_entity_id': 'candidate-1',
            'owner_module': 'communications',
            'proposed_action_family': 'enqueue_communication',
            'title': 'Follow up with candidate',
            'summary': 'Recommend scheduling a follow-up email.',
            'confidence_score': '0.92',
            'payload_json': {
                'channel': 'email',
                'recipient_email': 'candidate@example.com',
                'subject': 'Follow up',
                'body': 'Checking in on your application.',
            },
            'rationale_json': {'signals': ['inactive_48h']},
            'audit_metadata_json': {'source': 'unit_test'},
            'manual_override_allowed': True,
            'idempotency_key': f'suggestion-{uuid.uuid4()}',
        }
        payload.update(overrides)
        return payload

    def _create_suggestion(self, *, tenant_id=None, created_by=None, **overrides):
        suggestion, _ = SuggestionService.create_suggestion(
            tenant_id=tenant_id or self.tenant_id,
            created_by=created_by or self.user.id,
            suggestion_data=self._suggestion_payload(**overrides),
        )
        return suggestion

    def test_policy_crud_permission_and_tenant_isolation(self):
        create_payload = {
            'suggestion_type': 'followup_recommendation',
            'module_scope': 'communications',
            'confidence_threshold': '0.85',
            'auto_approve': True,
            'auto_apply': False,
            'approval_required': True,
            'is_enabled': True,
            'priority_order': 10,
        }
        create_response = self._call_view(
            AutomationIntelligencePolicyListCreateView,
            'post',
            '/api/v1/intelligence/automation-intelligence/policies/',
            self.user,
            data=create_payload,
        )
        self.assertEqual(create_response.status_code, 201)
        policy_id = create_response.data['data']['id']

        forbidden_response = self._call_view(
            AutomationIntelligencePolicyListCreateView,
            'post',
            '/api/v1/intelligence/automation-intelligence/policies/',
            self.hr_manager,
            data=create_payload | {'module_scope': 'pipeline'},
        )
        self.assertEqual(forbidden_response.status_code, 403)

        hidden_response = self._call_view(
            AutomationIntelligencePolicyDetailView,
            'get',
            f'/api/v1/intelligence/automation-intelligence/policies/{policy_id}/',
            self.other_tenant_user,
            pk=policy_id,
        )
        self.assertEqual(hidden_response.status_code, 404)

    def test_auto_approve_when_threshold_matches(self):
        AutomationIntelligencePolicy.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user.id,
            suggestion_type='followup_recommendation',
            module_scope='communications',
            confidence_threshold='0.85',
            auto_approve=True,
            auto_apply=False,
            approval_required=True,
        )
        suggestion = self._create_suggestion(confidence_score='0.90')
        result = AutomationIntelligenceService.evaluate_suggestion_policy(suggestion_id=suggestion.id)
        suggestion.refresh_from_db()
        self.assertEqual(result['status'], 'evaluated')
        self.assertEqual(suggestion.status, 'approved')

    def test_auto_apply_when_configured(self):
        AutomationIntelligencePolicy.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user.id,
            suggestion_type='followup_recommendation',
            module_scope='communications',
            confidence_threshold='0.80',
            auto_approve=True,
            auto_apply=True,
            approval_required=False,
        )
        suggestion = self._create_suggestion(confidence_score='0.91')

        class ApplyResult:
            retry_safe = True
            target_type = 'email_dispatch'
            target_id = None

            def execution_status(self):
                return 'completed'

            def as_contract_payload(self):
                return {'status': 'queued'}

        with patch(
            'apps.orchestration_center.services.suggestion_service.SuggestionService._execute_apply',
            return_value=ApplyResult(),
        ):
            result = AutomationIntelligenceService.evaluate_suggestion_policy(suggestion_id=suggestion.id)
        suggestion.refresh_from_db()
        self.assertEqual(result['status'], 'evaluated')
        self.assertEqual(suggestion.status, 'applied')

    def test_threshold_enforcement_and_fallback_behavior(self):
        AutomationIntelligencePolicy.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user.id,
            suggestion_type='followup_recommendation',
            module_scope='communications',
            confidence_threshold='0.95',
            auto_approve=True,
            auto_apply=False,
            approval_required=True,
        )
        suggestion = self._create_suggestion(confidence_score='0.80')
        result = AutomationIntelligenceService.evaluate_suggestion_policy(suggestion_id=suggestion.id)
        suggestion.refresh_from_db()
        self.assertEqual(result['status'], 'no_matching_policy')
        self.assertEqual(suggestion.status, 'pending')

    def test_disabled_policy_is_skipped(self):
        AutomationIntelligencePolicy.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user.id,
            suggestion_type='followup_recommendation',
            module_scope='communications',
            confidence_threshold='0.80',
            auto_approve=True,
            auto_apply=False,
            approval_required=True,
            is_enabled=False,
        )
        suggestion = self._create_suggestion(confidence_score='0.92')
        result = AutomationIntelligenceService.evaluate_suggestion_policy(suggestion_id=suggestion.id)
        suggestion.refresh_from_db()
        self.assertEqual(result['status'], 'no_matching_policy')
        self.assertEqual(suggestion.status, 'pending')

    def test_auto_apply_blocked_when_not_safe(self):
        AutomationIntelligencePolicy.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user.id,
            suggestion_type='followup_recommendation',
            module_scope='communications',
            confidence_threshold='0.80',
            auto_approve=True,
            auto_apply=True,
            approval_required=False,
        )
        suggestion = self._create_suggestion(
            confidence_score='0.91',
            manual_override_allowed=False,
        )
        result = AutomationIntelligenceService.evaluate_suggestion_policy(suggestion_id=suggestion.id)
        suggestion.refresh_from_db()
        self.assertEqual(result['status'], 'evaluated')
        self.assertTrue(result['auto_approved'])
        self.assertFalse(result['auto_applied'])
        self.assertEqual(result['outcome'], 'auto_apply_blocked')
        self.assertEqual(result['blocked_reason'], 'manual_override_not_allowed')
        # Suggestion was auto-approved but not applied.
        self.assertEqual(suggestion.status, 'approved')

    def test_safe_category_auto_applies_successfully(self):
        """followup_recommendation is in AutoApplyGuard.SAFE_CATEGORIES and should auto-apply."""
        AutomationIntelligencePolicy.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user.id,
            suggestion_type='followup_recommendation',
            module_scope='communications',
            confidence_threshold='0.80',
            auto_approve=True,
            auto_apply=True,
            approval_required=False,
        )
        suggestion = self._create_suggestion(
            confidence_score='0.91',
            proposed_action_family='enqueue_communication',
            manual_override_allowed=True,
        )

        class ApplyResult:
            retry_safe = True
            target_type = 'email_dispatch'
            target_id = None

            def execution_status(self):
                return 'completed'

            def as_contract_payload(self):
                return {'status': 'queued'}

        with patch(
            'apps.orchestration_center.services.suggestion_service.SuggestionService._execute_apply',
            return_value=ApplyResult(),
        ):
            result = AutomationIntelligenceService.evaluate_suggestion_policy(suggestion_id=suggestion.id)
        suggestion.refresh_from_db()
        self.assertEqual(result['status'], 'evaluated')
        self.assertTrue(result['auto_approved'])
        self.assertTrue(result['auto_applied'])
        self.assertEqual(result['outcome'], 'auto_applied')
        self.assertIsNone(result['blocked_reason'])
        self.assertEqual(suggestion.status, 'applied')

    def test_blocked_category_prevents_auto_apply(self):
        """escalation_recommendation is not in AutoApplyGuard.SAFE_CATEGORIES — guard blocks apply."""
        AutomationIntelligencePolicy.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user.id,
            suggestion_type='escalation_recommendation',
            module_scope='communications',
            confidence_threshold='0.80',
            auto_approve=True,
            auto_apply=True,
            approval_required=False,
        )
        suggestion = self._create_suggestion(
            category='escalation_recommendation',
            confidence_score='0.91',
        )
        result = AutomationIntelligenceService.evaluate_suggestion_policy(suggestion_id=suggestion.id)
        suggestion.refresh_from_db()
        self.assertEqual(result['status'], 'evaluated')
        self.assertTrue(result['auto_approved'])
        self.assertFalse(result['auto_applied'])
        self.assertEqual(result['outcome'], 'auto_apply_blocked')
        self.assertIsNotNone(result['blocked_reason'])
        self.assertIn('category_not_in_safe_list', result['blocked_reason'])
        # Suggestion was approved but NOT applied.
        self.assertEqual(suggestion.status, 'approved')

    def test_auto_apply_failure_is_non_blocking(self):
        """OwnerContractError during apply should not propagate — outcome is auto_apply_failed."""
        AutomationIntelligencePolicy.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user.id,
            suggestion_type='followup_recommendation',
            module_scope='communications',
            confidence_threshold='0.80',
            auto_approve=True,
            auto_apply=True,
            approval_required=False,
        )
        suggestion = self._create_suggestion(
            confidence_score='0.91',
            manual_override_allowed=True,
        )
        with patch(
            'apps.orchestration_center.services.suggestion_service.SuggestionService._execute_apply',
            side_effect=OwnerContractError.validation('Contract failed in test'),
        ):
            result = AutomationIntelligenceService.evaluate_suggestion_policy(suggestion_id=suggestion.id)
        suggestion.refresh_from_db()
        self.assertEqual(result['status'], 'evaluated')
        self.assertTrue(result['auto_approved'])
        self.assertFalse(result['auto_applied'])
        self.assertEqual(result['outcome'], 'auto_apply_failed')
        self.assertEqual(suggestion.status, 'apply_failed')

    def test_suggestion_creation_schedules_async_policy_evaluation(self):
        with patch(
            'apps.orchestration_center.tasks.automation_intelligence_tasks.evaluate_suggestion_policy_task.delay'
        ) as mocked_delay:
            with self.captureOnCommitCallbacks(execute=True):
                suggestion = self._create_suggestion(confidence_score='0.88')
        mocked_delay.assert_called_once_with(str(suggestion.id))
