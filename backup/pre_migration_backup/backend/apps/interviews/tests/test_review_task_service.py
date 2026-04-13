import uuid

from django.test import TestCase

from apps.interviews.services import InterviewReviewTaskService
from apps.interviews.models import InterviewReviewTask
from shared.owner_contracts import OwnerActionContext, OwnerContractError


class InterviewReviewTaskServiceTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.interview_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

    def test_create_task_is_idempotent_for_same_external_reference(self):
        task, created = InterviewReviewTaskService.create_task(
            tenant_id=self.tenant_id,
            interview_id=self.interview_id,
            review_type='interview_feedback_review',
            requested_by=self.user_id,
            assigned_role='hr_manager',
            external_reference='review-task-dedupe',
        )
        duplicate, duplicate_created = InterviewReviewTaskService.create_task(
            tenant_id=self.tenant_id,
            interview_id=self.interview_id,
            review_type='interview_feedback_review',
            requested_by=self.user_id,
            assigned_role='hr_manager',
            external_reference='review-task-dedupe',
        )

        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(task.id, duplicate.id)
        self.assertEqual(
            InterviewReviewTask.objects.filter(
                tenant_id=self.tenant_id,
                interview_id=self.interview_id,
                review_type='interview_feedback_review',
                external_reference='review-task-dedupe',
            ).count(),
            1,
        )

    def test_assign_task_is_idempotent(self):
        task, _ = InterviewReviewTaskService.create_task(
            tenant_id=self.tenant_id,
            interview_id=self.interview_id,
            review_type='interview_feedback_review',
            requested_by=self.user_id,
            assigned_role='hr_manager',
            external_reference='review-task-assign',
        )
        assigned, created = InterviewReviewTaskService.assign_task(
            tenant_id=self.tenant_id,
            interview_id=self.interview_id,
            review_type='interview_feedback_review',
            assigned_reviewer_id=self.user_id,
            assigned_role='reviewer',
            external_reference='review-task-assign',
        )
        duplicate, duplicate_created = InterviewReviewTaskService.assign_task(
            tenant_id=self.tenant_id,
            interview_id=self.interview_id,
            review_type='interview_feedback_review',
            assigned_reviewer_id=self.user_id,
            assigned_role='reviewer',
            external_reference='review-task-assign',
        )

        self.assertEqual(task.id, assigned.id)
        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(duplicate.assigned_reviewer_id, self.user_id)

    def test_mark_operational_flag_is_idempotent_for_review_task(self):
        task, _ = InterviewReviewTaskService.create_task(
            tenant_id=self.tenant_id,
            interview_id=self.interview_id,
            review_type='interview_feedback_review',
            requested_by=self.user_id,
            external_reference='review-task-flag',
        )
        flagged, created = InterviewReviewTaskService.mark_operational_flag(
            tenant_id=self.tenant_id,
            entity_type='review_task',
            entity_id=task.id,
            flag_key='manual_check_required',
            flag_value=True,
            metadata={'source': 'test'},
        )
        duplicate, duplicate_created = InterviewReviewTaskService.mark_operational_flag(
            tenant_id=self.tenant_id,
            entity_type='review_task',
            entity_id=task.id,
            flag_key='manual_check_required',
            flag_value=True,
            metadata={'source': 'test'},
        )

        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(flagged.id, duplicate.id)
        self.assertTrue(flagged.metadata['operational_flags']['manual_check_required']['value'])

    def test_create_automation_review_task_stores_owner_and_governance_metadata(self):
        task, created = InterviewReviewTaskService.create_automation_review_task(
            tenant_id=self.tenant_id,
            owner_module='ai_execution',
            entity_type='ai_execution',
            entity_id=self.interview_id,
            review_type='ai_output_review',
            requested_by=self.user_id,
            assigned_role='hr_manager',
            approval_required=True,
            approver_role='tenant_admin',
            external_reference='automation-review-dedupe',
        )
        duplicate, duplicate_created = InterviewReviewTaskService.create_automation_review_task(
            tenant_id=self.tenant_id,
            owner_module='ai_execution',
            entity_type='ai_execution',
            entity_id=self.interview_id,
            review_type='ai_output_review',
            requested_by=self.user_id,
            assigned_role='hr_manager',
            approval_required=True,
            approver_role='tenant_admin',
            external_reference='automation-review-dedupe',
        )

        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(task.id, duplicate.id)
        self.assertEqual(task.metadata['owner_module'], 'ai_execution')
        self.assertEqual(task.metadata['entity_type'], 'ai_execution')
        self.assertEqual(task.metadata['entity_id'], str(self.interview_id))
        self.assertTrue(task.metadata['governance']['approval_required'])

    def test_create_from_orchestration_returns_normalized_duplicate_result(self):
        context = OwnerActionContext(
            tenant_id=self.tenant_id,
            actor_id=self.user_id,
            external_reference='review-task-contract-dedupe',
            audit_metadata={'automation_run_id': 'run-1', 'rule_id': 'rule-1'},
        )

        first = InterviewReviewTaskService.create_from_orchestration(
            context=context,
            owner_module='interviews',
            entity_type='interview',
            entity_id=self.interview_id,
            review_type='interview_feedback_review',
            assigned_role='hr_manager',
        )
        second = InterviewReviewTaskService.create_from_orchestration(
            context=context,
            owner_module='interviews',
            entity_type='interview',
            entity_id=self.interview_id,
            review_type='interview_feedback_review',
            assigned_role='hr_manager',
        )

        self.assertFalse(first.duplicate)
        self.assertTrue(second.duplicate)
        self.assertEqual(second.execution_status(), 'deduplicated')
        self.assertEqual(second.payload['review_type'], 'interview_feedback_review')

    def test_create_from_orchestration_uses_structured_owner_error_for_unsupported_type(self):
        with self.assertRaises(OwnerContractError) as exc_info:
            InterviewReviewTaskService.create_from_orchestration(
                context=OwnerActionContext(
                    tenant_id=self.tenant_id,
                    actor_id=self.user_id,
                    external_reference='review-task-contract-error',
                    audit_metadata={'automation_run_id': 'run-1'},
                ),
                owner_module='interviews',
                entity_type='interview',
                entity_id=self.interview_id,
                review_type='unsupported_review_type',
            )

        self.assertEqual(exc_info.exception.error_category, OwnerContractError.CATEGORY_UNSUPPORTED)
        self.assertFalse(exc_info.exception.retry_safe)
