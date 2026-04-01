import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.candidates.models import Candidate, CandidateEngagement, CandidateTimelineEvent
from apps.candidates.services import CandidateAssignmentService, CandidateOperationalFlagService


class CandidateAssignmentServiceTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.other_tenant_id = uuid.uuid4()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='candidate-owner-test@example.com',
            password='testpass123',
            tenant_id=self.tenant_id,
            role='recruiter',
        )
        self.assignee = user_model.objects.create_user(
            email='candidate-assignee-test@example.com',
            password='testpass123',
            tenant_id=self.tenant_id,
            role='recruiter',
        )
        self.user_id = self.user.id
        self.assignee_id = self.assignee.id
        self.candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Asha',
            last_name='Menon',
            email='asha@example.com',
            phone='+919999999999',
            created_by=self.user_id,
        )
        self.engagement = CandidateEngagement.objects.create(
            tenant_id=self.tenant_id,
            candidate=self.candidate,
            engagement_type='lead',
            stage='new_lead',
            priority='warm',
            is_active=True,
        )

    def test_assign_candidate_owner_updates_candidate_and_active_engagement(self):
        candidate, engagement, created = CandidateAssignmentService.assign_candidate_owner(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            owner_user_id=self.assignee_id,
            assigned_by=self.user_id,
            assignment_reason='automation_rule',
            external_reference='candidate-assign-1',
        )

        self.assertTrue(created)
        self.assertEqual(candidate.owner_user_id, self.assignee_id)
        self.assertEqual(engagement.owner_user_id, self.assignee_id)
        self.assertEqual(
            CandidateTimelineEvent.objects.filter(
                tenant_id=self.tenant_id,
                candidate=self.candidate,
                event_type='candidate.assigned',
            ).count(),
            1,
        )

    def test_assign_candidate_owner_is_idempotent_for_same_owner(self):
        CandidateAssignmentService.assign_candidate_owner(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            owner_user_id=self.assignee_id,
            assigned_by=self.user_id,
            external_reference='candidate-assign-2',
        )
        candidate, engagement, created = CandidateAssignmentService.assign_candidate_owner(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            owner_user_id=self.assignee_id,
            assigned_by=self.user_id,
            external_reference='candidate-assign-2',
        )

        self.assertFalse(created)
        self.assertEqual(candidate.owner_user_id, self.assignee_id)
        self.assertEqual(engagement.owner_user_id, self.assignee_id)
        self.assertEqual(
            CandidateTimelineEvent.objects.filter(
                tenant_id=self.tenant_id,
                candidate=self.candidate,
                event_type='candidate.assigned',
            ).count(),
            1,
        )

    def test_assign_candidate_owner_preserves_tenant_isolation(self):
        with self.assertRaisesMessage(ValueError, 'Candidate not found for assignment.'):
            CandidateAssignmentService.assign_candidate_owner(
                tenant_id=self.other_tenant_id,
                candidate_id=self.candidate.id,
                owner_user_id=self.assignee_id,
                assigned_by=self.user_id,
            )

    def test_assign_from_orchestration_rejects_cross_tenant_assignee(self):
        other_tenant_assignee = get_user_model().objects.create_user(
            email='candidate-other-tenant@example.com',
            password='testpass123',
            tenant_id=self.other_tenant_id,
            role='recruiter',
        )

        with self.assertRaises(OwnerContractError) as exc_info:
            CandidateAssignmentService.assign_from_orchestration(
                context=OwnerActionContext(
                    tenant_id=self.tenant_id,
                    actor_id=self.user_id,
                    external_reference='candidate-contract-owner-check',
                    audit_metadata={'automation_run_id': 'run-1'},
                ),
                candidate_id=self.candidate.id,
                owner_user_id=other_tenant_assignee.id,
            )

        self.assertEqual(exc_info.exception.error_category, OwnerContractError.CATEGORY_OWNERSHIP)
        self.assertFalse(exc_info.exception.retry_safe)

    def test_mark_operational_flag_updates_candidate_and_active_engagement(self):
        candidate, engagement, created = CandidateOperationalFlagService.mark_operational_flag(
            tenant_id=self.tenant_id,
            entity_type='candidate',
            entity_id=self.candidate.id,
            flag_key='attention_needed',
            flag_value=True,
            metadata={'reason': 'automation'},
            external_reference='candidate-flag-1',
        )

        self.assertTrue(created)
        self.assertTrue(candidate.metadata['operational_flags']['attention_needed']['value'])
        self.assertTrue(engagement.metadata['operational_flags']['attention_needed']['value'])
        self.assertEqual(
            CandidateTimelineEvent.objects.filter(
                tenant_id=self.tenant_id,
                candidate=self.candidate,
                event_type='candidate.flagged',
            ).count(),
            1,
        )

    def test_mark_operational_flag_is_idempotent(self):
        CandidateOperationalFlagService.mark_operational_flag(
            tenant_id=self.tenant_id,
            entity_type='candidate',
            entity_id=self.candidate.id,
            flag_key='review_required',
            flag_value=True,
            metadata={'reason': 'automation'},
            external_reference='candidate-flag-2',
        )

        candidate, engagement, created = CandidateOperationalFlagService.mark_operational_flag(
            tenant_id=self.tenant_id,
            entity_type='candidate',
            entity_id=self.candidate.id,
            flag_key='review_required',
            flag_value=True,
            metadata={'reason': 'automation'},
            external_reference='candidate-flag-2',
        )

        self.assertFalse(created)
        self.assertTrue(candidate.metadata['operational_flags']['review_required']['value'])
        self.assertTrue(engagement.metadata['operational_flags']['review_required']['value'])
        self.assertEqual(
            CandidateTimelineEvent.objects.filter(
                tenant_id=self.tenant_id,
                candidate=self.candidate,
                event_type='candidate.flagged',
            ).count(),
            1,
        )

    def test_mark_operational_flag_preserves_tenant_isolation(self):
        with self.assertRaisesMessage(ValueError, 'Candidate not found for flagging.'):
            CandidateOperationalFlagService.mark_operational_flag(
                tenant_id=self.other_tenant_id,
                entity_type='candidate',
                entity_id=self.candidate.id,
                flag_key='manual_check_required',
                flag_value=True,
            )
from shared.owner_contracts import OwnerActionContext, OwnerContractError
