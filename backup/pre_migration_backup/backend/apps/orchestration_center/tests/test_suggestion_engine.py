import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.orchestration_center.api.views import (
    SuggestionApproveView,
    SuggestionApplyView,
    SuggestionDetailView,
    SuggestionDismissView,
    SuggestionListCreateView,
    SuggestionRejectView,
)
from apps.orchestration_center.constants.execution_statuses import ApprovalStatus, SuggestionStatus
from apps.orchestration_center.models import AISuggestion, IntelligenceAuditLog, TenantIntelligenceSettings
from apps.orchestration_center.services.suggestion_service import SuggestionService
from shared.owner_contracts import OwnerContractError


class AISuggestionGovernanceApiTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.UUID('00000000-0000-0000-0000-000000000111')
        self.other_tenant_id = uuid.UUID('00000000-0000-0000-0000-000000000222')
        self.user = get_user_model().objects.create_user(
            email='tenant-admin@example.com',
            password='password',
            tenant_id=self.tenant_id,
            role='tenant_admin',
            is_staff=True,
        )
        self.hr_manager = get_user_model().objects.create_user(
            email='hr-manager@example.com',
            password='password',
            tenant_id=self.tenant_id,
            role='hr_manager',
            is_staff=True,
        )
        self.recruiter = get_user_model().objects.create_user(
            email='recruiter@example.com',
            password='password',
            tenant_id=self.tenant_id,
            role='recruiter',
            is_staff=True,
        )
        self.other_user = get_user_model().objects.create_user(
            email='other-tenant-admin@example.com',
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
            'confidence_score': '0.82',
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

    def test_create_and_list_suggestions_are_tenant_scoped(self):
        response = self._call_view(
            SuggestionListCreateView,
            'post',
            '/api/v1/intelligence/suggestions/',
            self.user,
            data=self._suggestion_payload(),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['status'], SuggestionStatus.PENDING)
        self.assertEqual(response.data['data']['confidence_band'], 'high')

        other_suggestion = self._create_suggestion(tenant_id=self.other_tenant_id, created_by=self.other_user.id)

        list_response = self._call_view(
            SuggestionListCreateView,
            'get',
            '/api/v1/intelligence/suggestions/',
            self.user,
        )
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data['data']), 1)
        self.assertEqual(list_response.data['data'][0]['tenant_id'], str(self.tenant_id))

        detail_response = self._call_view(
            SuggestionDetailView,
            'get',
            f'/api/v1/intelligence/suggestions/{other_suggestion.id}/',
            self.user,
            pk=other_suggestion.id,
        )
        self.assertEqual(detail_response.status_code, 404)

    def test_create_requires_approval_builds_governance_item_but_stays_pending(self):
        response = self._call_view(
            SuggestionListCreateView,
            'post',
            '/api/v1/intelligence/suggestions/',
            self.user,
            data=self._suggestion_payload(
                requires_approval=True,
                owner_module='pipeline',
                proposed_action_family='create_deadline',
            ),
        )
        self.assertEqual(response.status_code, 201)
        suggestion = AISuggestion.objects.get(pk=response.data['data']['id'])
        self.assertEqual(suggestion.status, SuggestionStatus.PENDING)
        self.assertIsNotNone(suggestion.approval_item_id)
        self.assertEqual(suggestion.approval_item.status, ApprovalStatus.PENDING)

    def test_approve_reject_and_dismiss_flows_are_audited(self):
        approval_target = self._create_suggestion(requires_approval=True)
        dismissal_target = self._create_suggestion(requires_approval=False)
        rejection_target = self._create_suggestion(requires_approval=False)

        approve_response = self._call_view(
            SuggestionApproveView,
            'post',
            f'/api/v1/intelligence/suggestions/{approval_target.id}/approve/',
            self.hr_manager,
            data={'comment': 'Governance cleared.'},
            pk=approval_target.id,
        )
        self.assertEqual(approve_response.status_code, 200)
        approval_target.refresh_from_db()
        self.assertEqual(approval_target.status, SuggestionStatus.APPROVED)
        self.assertEqual(approval_target.approval_item.status, ApprovalStatus.APPROVED)

        dismiss_response = self._call_view(
            SuggestionDismissView,
            'post',
            f'/api/v1/intelligence/suggestions/{dismissal_target.id}/dismiss/',
            self.hr_manager,
            data={'comment': 'No longer needed.'},
            pk=dismissal_target.id,
        )
        self.assertEqual(dismiss_response.status_code, 200)
        dismissal_target.refresh_from_db()
        self.assertEqual(dismissal_target.status, SuggestionStatus.DISMISSED)
        self.assertEqual(dismissal_target.dismissed_by_id, self.hr_manager.id)

        reject_response = self._call_view(
            SuggestionRejectView,
            'post',
            f'/api/v1/intelligence/suggestions/{rejection_target.id}/reject/',
            self.hr_manager,
            data={'comment': 'Not appropriate for this tenant.'},
            pk=rejection_target.id,
        )
        self.assertEqual(reject_response.status_code, 200)
        rejection_target.refresh_from_db()
        self.assertEqual(rejection_target.status, SuggestionStatus.REJECTED)
        self.assertEqual(rejection_target.rejected_by_id, self.hr_manager.id)
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_suggestion',
                target_id=rejection_target.id,
                action_type='ai_suggestion.rejected',
            ).exists()
        )

    def test_permission_enforcement_respects_tenant_role_overrides(self):
        suggestion = self._create_suggestion(requires_approval=True)
        TenantIntelligenceSettings.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user.id,
            updated_by_id=self.user.id,
            visibility_permissions_json={
                'suggestion_approve_roles': ['tenant_admin'],
                'suggestion_reject_roles': ['tenant_admin'],
                'suggestion_dismiss_roles': ['tenant_admin'],
            },
        )

        approve_response = self._call_view(
            SuggestionApproveView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/approve/',
            self.hr_manager,
            data={'comment': 'Attempted approval.'},
            pk=suggestion.id,
        )
        self.assertEqual(approve_response.status_code, 403)

    def test_invalid_transition_rejected_for_approve_on_non_pending(self):
        suggestion = self._create_suggestion(requires_approval=False)
        SuggestionService.approve_suggestion(suggestion=suggestion, user_id=self.user.id, comment='Approved once')
        response = self._call_view(
            SuggestionApproveView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/approve/',
            self.user,
            data={'comment': 'Should fail because already approved.'},
            pk=suggestion.id,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('only pending suggestions', str(response.data['message']).lower())

    def test_tenant_isolation_blocks_cross_tenant_approve(self):
        suggestion = self._create_suggestion(requires_approval=False)
        response = self._call_view(
            SuggestionApproveView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/approve/',
            self.other_user,
            data={'comment': 'Cross tenant approve attempt.'},
            pk=suggestion.id,
        )
        self.assertEqual(response.status_code, 404)

    def test_audit_creation_for_approve_reject_and_dismiss(self):
        approved = self._create_suggestion(requires_approval=False)
        rejected = self._create_suggestion(requires_approval=False)
        dismissed = self._create_suggestion(requires_approval=False)

        approve_response = self._call_view(
            SuggestionApproveView,
            'post',
            f'/api/v1/intelligence/suggestions/{approved.id}/approve/',
            self.hr_manager,
            data={'comment': 'Approve for audit test.'},
            pk=approved.id,
        )
        self.assertEqual(approve_response.status_code, 200)
        reject_response = self._call_view(
            SuggestionRejectView,
            'post',
            f'/api/v1/intelligence/suggestions/{rejected.id}/reject/',
            self.hr_manager,
            data={'comment': 'Reject for audit test.'},
            pk=rejected.id,
        )
        self.assertEqual(reject_response.status_code, 200)
        dismiss_response = self._call_view(
            SuggestionDismissView,
            'post',
            f'/api/v1/intelligence/suggestions/{dismissed.id}/dismiss/',
            self.hr_manager,
            data={'comment': 'Dismiss for audit test.'},
            pk=dismissed.id,
        )
        self.assertEqual(dismiss_response.status_code, 200)

        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_suggestion',
                target_id=approved.id,
                action_type='ai_suggestion.approved',
            ).exists()
        )
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_suggestion',
                target_id=rejected.id,
                action_type='ai_suggestion.rejected',
            ).exists()
        )
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_suggestion',
                target_id=dismissed.id,
                action_type='ai_suggestion.dismissed',
            ).exists()
        )

    def test_apply_success_from_approved_status(self):
        suggestion = self._create_suggestion(requires_approval=False)
        SuggestionService.approve_suggestion(suggestion=suggestion, user_id=self.hr_manager.id, comment='Approved first')

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
            response = self._call_view(
                SuggestionApplyView,
                'post',
                f'/api/v1/intelligence/suggestions/{suggestion.id}/apply/',
                self.hr_manager,
                data={'comment': 'Apply now.'},
                pk=suggestion.id,
            )

        self.assertEqual(response.status_code, 200)
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, SuggestionStatus.APPLIED)
        self.assertEqual(suggestion.applied_by_id, self.hr_manager.id)
        self.assertEqual(suggestion.last_apply_status, 'completed')
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_suggestion',
                target_id=suggestion.id,
                action_type='ai_suggestion.applied',
            ).exists()
        )

    def test_apply_failure_is_non_blocking_and_marks_apply_failed(self):
        suggestion = self._create_suggestion(requires_approval=False)
        SuggestionService.approve_suggestion(suggestion=suggestion, user_id=self.hr_manager.id, comment='Approved first')

        with patch(
            'apps.orchestration_center.services.suggestion_service.SuggestionService._execute_apply',
            side_effect=OwnerContractError.unsupported('No owner contract'),
        ):
            response = self._call_view(
                SuggestionApplyView,
                'post',
                f'/api/v1/intelligence/suggestions/{suggestion.id}/apply/',
                self.hr_manager,
                data={'comment': 'Apply now.'},
                pk=suggestion.id,
            )

        self.assertEqual(response.status_code, 200)
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, SuggestionStatus.APPLY_FAILED)
        self.assertEqual(suggestion.last_apply_status, SuggestionStatus.APPLY_FAILED)
        self.assertIn('No owner contract', suggestion.last_apply_error_message)
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_suggestion',
                target_id=suggestion.id,
                action_type='ai_suggestion.apply_failed',
            ).exists()
        )

    def test_apply_rejects_invalid_status_transition(self):
        suggestion = self._create_suggestion(requires_approval=False)
        response = self._call_view(
            SuggestionApplyView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/apply/',
            self.hr_manager,
            data={'comment': 'Apply pending should fail.'},
            pk=suggestion.id,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('must be approved', str(response.data['message']).lower())

    def test_apply_permission_enforcement_respects_tenant_role_overrides(self):
        suggestion = self._create_suggestion(requires_approval=False)
        SuggestionService.approve_suggestion(suggestion=suggestion, user_id=self.user.id, comment='Approved for apply test')
        TenantIntelligenceSettings.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user.id,
            updated_by_id=self.user.id,
            visibility_permissions_json={
                'suggestion_apply_roles': ['tenant_admin'],
            },
        )

        response = self._call_view(
            SuggestionApplyView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/apply/',
            self.hr_manager,
            data={'comment': 'Apply should be forbidden.'},
            pk=suggestion.id,
        )
        self.assertEqual(response.status_code, 403)

    def test_tenant_isolation_blocks_cross_tenant_apply(self):
        suggestion = self._create_suggestion(requires_approval=False)
        SuggestionService.approve_suggestion(suggestion=suggestion, user_id=self.user.id, comment='Approved first')
        response = self._call_view(
            SuggestionApplyView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/apply/',
            self.other_user,
            data={'comment': 'Cross tenant apply attempt.'},
            pk=suggestion.id,
        )
        self.assertEqual(response.status_code, 404)

    def test_applied_status_and_traceability_visible_in_detail(self):
        suggestion = self._create_suggestion(requires_approval=False)
        SuggestionService.approve_suggestion(suggestion=suggestion, user_id=self.user.id, comment='Approved first')
        target_id = uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')

        class ApplyResult:
            retry_safe = True
            target_type = 'email_dispatch'

            def __init__(self, resolved_target_id):
                self.target_id = resolved_target_id

            def execution_status(self):
                return 'completed'

            def as_contract_payload(self):
                return {'dispatch_id': 'disp-1', 'queued': True}

        with patch(
            'apps.orchestration_center.services.suggestion_service.SuggestionService._execute_apply',
            return_value=ApplyResult(target_id),
        ):
            apply_response = self._call_view(
                SuggestionApplyView,
                'post',
                f'/api/v1/intelligence/suggestions/{suggestion.id}/apply/',
                self.hr_manager,
                data={'comment': 'Apply traceability test'},
                pk=suggestion.id,
            )
        self.assertEqual(apply_response.status_code, 200)

        detail_response = self._call_view(
            SuggestionDetailView,
            'get',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/',
            self.hr_manager,
            pk=suggestion.id,
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data['data']['status'], SuggestionStatus.APPLIED)
        self.assertEqual(detail_response.data['data']['converted_artifact_type'], 'email_dispatch')
        self.assertEqual(detail_response.data['data']['converted_artifact_id'], str(target_id))
        self.assertEqual(detail_response.data['data']['last_apply_result_json']['owner_module'], 'communications')
        self.assertEqual(detail_response.data['data']['last_apply_result_json']['proposed_action_family'], 'enqueue_communication')

    def test_apply_failed_visibility_in_detail_includes_failure_reason_and_retry_flag(self):
        suggestion = self._create_suggestion(requires_approval=False)
        SuggestionService.approve_suggestion(suggestion=suggestion, user_id=self.user.id, comment='Approved first')

        with patch(
            'apps.orchestration_center.services.suggestion_service.SuggestionService._execute_apply',
            side_effect=OwnerContractError.unsupported('Unsupported downstream action'),
        ):
            apply_response = self._call_view(
                SuggestionApplyView,
                'post',
                f'/api/v1/intelligence/suggestions/{suggestion.id}/apply/',
                self.hr_manager,
                data={'comment': 'Failure traceability test'},
                pk=suggestion.id,
            )
        self.assertEqual(apply_response.status_code, 200)

        detail_response = self._call_view(
            SuggestionDetailView,
            'get',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/',
            self.hr_manager,
            pk=suggestion.id,
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data['data']['status'], SuggestionStatus.APPLY_FAILED)
        self.assertIn('Unsupported downstream action', detail_response.data['data']['last_apply_error_message'])
        self.assertEqual(detail_response.data['data']['last_apply_result_json']['retry_safe'], False)
