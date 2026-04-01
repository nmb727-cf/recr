import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.communications.models import Notification
from apps.orchestration_center.api.views import (
    SuggestionApproveView,
    SuggestionConvertView,
    SuggestionDetailView,
    SuggestionListCreateView,
    SuggestionReviewView,
)
from apps.orchestration_center.constants.execution_statuses import ApprovalStatus, SuggestionStatus
from apps.orchestration_center.models import AISuggestion, AISuggestionConversion, ApprovalQueueItem, IntelligenceAuditLog
from apps.orchestration_center.services.suggestion_service import SuggestionService
from apps.pipeline.models import ActionDeadline


class AISuggestionEngineApiTests(TestCase):
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
            'source_module': 'candidates',
            'source_entity_type': 'candidate',
            'source_entity_id': 'candidate-1',
            'owner_module': 'communications',
            'proposed_action_family': 'enqueue_communication',
            'title': 'Follow up with candidate',
            'summary': 'Recommend scheduling a follow-up email.',
            'confidence_score': '0.82',
            'payload_json': {'channel': 'email', 'template_key': 'followup'},
            'rationale_json': {'signals': ['inactive_48h']},
            'audit_metadata_json': {'source': 'unit_test'},
            'manual_override_allowed': True,
            'idempotency_key': 'suggestion-candidate-followup',
        }
        payload.update(overrides)
        return payload

    def _create_suggestion(self, *, tenant_id=None, created_by=None, **overrides):
        suggestion, _ = SuggestionService.create_suggestion(
            tenant_id=tenant_id or self.tenant_id,
            created_by=created_by or self.user.id,
            suggestion_data={
                'suggestion_key': overrides.pop('suggestion_key', 'candidate-escalation'),
                'category': overrides.pop('category', 'escalation_recommendation'),
                'source_event': overrides.pop('source_event', 'candidate.updated'),
                'source_module': overrides.pop('source_module', 'candidates'),
                'source_entity_type': overrides.pop('source_entity_type', 'candidate'),
                'source_entity_id': overrides.pop('source_entity_id', 'candidate-2'),
                'owner_module': overrides.pop('owner_module', 'pipeline'),
                'proposed_action_family': overrides.pop('proposed_action_family', 'create_deadline'),
                'title': overrides.pop('title', 'Create follow-up deadline'),
                'summary': overrides.pop('summary', 'Recommend a follow-up deadline.'),
                'payload_json': overrides.pop('payload_json', {'deadline_type': 'candidate_followup'}),
                'confidence_score': overrides.pop('confidence_score', '0.66'),
                'requires_approval': overrides.pop('requires_approval', False),
                'idempotency_key': overrides.pop('idempotency_key', f'suggestion-{uuid.uuid4()}'),
                **overrides,
            },
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
        self.assertEqual(response.data['data']['status'], SuggestionStatus.PENDING_REVIEW)
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

    def test_create_requires_approval_builds_governance_item(self):
        response = self._call_view(
            SuggestionListCreateView,
            'post',
            '/api/v1/intelligence/suggestions/',
            self.user,
            data=self._suggestion_payload(
                suggestion_key='deadline-review',
                proposed_action_family='create_deadline',
                owner_module='pipeline',
                requires_approval=True,
                idempotency_key='suggestion-deadline-review',
            ),
        )
        self.assertEqual(response.status_code, 201)
        suggestion = AISuggestion.objects.get(pk=response.data['data']['id'])
        self.assertEqual(suggestion.status, SuggestionStatus.PENDING_APPROVAL)
        self.assertIsNotNone(suggestion.approval_item_id)
        self.assertEqual(suggestion.approval_item.status, ApprovalStatus.PENDING)

    def test_review_and_approve_suggestion_are_audited(self):
        suggestion = self._create_suggestion()

        review_response = self._call_view(
            SuggestionReviewView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/review/',
            self.user,
            data={'status': SuggestionStatus.REJECTED, 'comment': 'Not relevant anymore.'},
            pk=suggestion.id,
        )
        self.assertEqual(review_response.status_code, 200)
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, SuggestionStatus.REJECTED)

        suggestion = self._create_suggestion(requires_approval=True, idempotency_key='suggestion-approval')
        approve_response = self._call_view(
            SuggestionApproveView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/approve/',
            self.user,
            data={'comment': 'Approved for operational follow-up.'},
            pk=suggestion.id,
        )
        self.assertEqual(approve_response.status_code, 200)
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, SuggestionStatus.APPROVED)
        self.assertEqual(suggestion.approval_item.status, ApprovalStatus.APPROVED)
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_suggestion',
                target_id=suggestion.id,
                action_type='ai_suggestion.approved',
            ).exists()
        )

    def test_convert_suggestion_is_non_mutating_and_idempotent(self):
        suggestion = self._create_suggestion(
            owner_module='communications',
            proposed_action_family='enqueue_communication',
            payload_json={'channel': 'email', 'template_key': 'followup'},
            idempotency_key='suggestion-convert-safe',
        )

        self.assertEqual(ActionDeadline.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)

        first = self._call_view(
            SuggestionConvertView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/convert/',
            self.user,
            data={'conversion_type': 'approval_queue_item', 'idempotency_key': 'convert-candidate-followup'},
            pk=suggestion.id,
        )
        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.data['data']['deduplicated'])
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, SuggestionStatus.CONVERTED)
        self.assertEqual(ActionDeadline.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(AISuggestionConversion.objects.filter(suggestion=suggestion).count(), 1)
        self.assertEqual(
            ApprovalQueueItem.objects.filter(tenant_id=self.tenant_id, origin_type='ai_suggestion', origin_id=suggestion.id).count(),
            1,
        )

        second = self._call_view(
            SuggestionConvertView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/convert/',
            self.user,
            data={'conversion_type': 'approval_queue_item', 'idempotency_key': 'convert-candidate-followup'},
            pk=suggestion.id,
        )
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data['data']['deduplicated'])
        self.assertEqual(AISuggestionConversion.objects.filter(suggestion=suggestion).count(), 1)
        self.assertEqual(ActionDeadline.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)

    def test_conversion_requires_approval_when_configured(self):
        suggestion = self._create_suggestion(
            requires_approval=True,
            proposed_action_family='create_deadline',
            owner_module='pipeline',
            idempotency_key='suggestion-requires-approval',
        )

        blocked = self._call_view(
            SuggestionConvertView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/convert/',
            self.user,
            data={'conversion_type': 'approval_queue_item'},
            pk=suggestion.id,
        )
        self.assertEqual(blocked.status_code, 400)
        self.assertIn('approval is required', blocked.data['message'].lower())

        approve = self._call_view(
            SuggestionApproveView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/approve/',
            self.user,
            data={'comment': 'Governance cleared.'},
            pk=suggestion.id,
        )
        self.assertEqual(approve.status_code, 200)

        converted = self._call_view(
            SuggestionConvertView,
            'post',
            f'/api/v1/intelligence/suggestions/{suggestion.id}/convert/',
            self.user,
            data={'conversion_type': 'approval_queue_item', 'override_payload_json': {'deadline_type': 'manager_followup'}},
            pk=suggestion.id,
        )
        self.assertEqual(converted.status_code, 200)
        conversion = AISuggestionConversion.objects.get(suggestion=suggestion)
        self.assertEqual(conversion.requested_action_payload_json['payload']['deadline_type'], 'manager_followup')
