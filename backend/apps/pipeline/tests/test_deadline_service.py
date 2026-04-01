import uuid

from django.test import TestCase

from apps.pipeline.models import ActionDeadline, Application
from apps.pipeline.services import PipelineDeadlineService
from shared.owner_contracts import OwnerActionContext


class PipelineDeadlineServiceTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.entity_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        self.application = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=uuid.uuid4(),
            requisition_id=uuid.uuid4(),
            status='applied',
            created_by=self.user_id,
        )

    def test_create_automation_deadline_is_idempotent_for_same_external_reference(self):
        deadline, created = PipelineDeadlineService.create_automation_deadline(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            due_in_hours=24,
            assigned_to=self.user_id,
            metadata={'deadline_type': 'review'},
            external_reference='runtime-test:create-deadline',
        )
        duplicate, duplicate_created = PipelineDeadlineService.create_automation_deadline(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            due_in_hours=24,
            assigned_to=self.user_id,
            metadata={'deadline_type': 'review'},
            external_reference='runtime-test:create-deadline',
        )

        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(deadline.id, duplicate.id)
        self.assertEqual(
            ActionDeadline.objects.filter(
                tenant_id=self.tenant_id,
                entity_type='application',
                entity_id=self.entity_id,
                metadata__external_source='orchestration_center',
                metadata__external_reference='runtime-test:create-deadline',
            ).count(),
            1,
        )

    def test_create_automation_deadline_requires_valid_uuid_entity_id(self):
        with self.assertRaisesMessage(ValueError, 'valid UUID entity_id'):
            PipelineDeadlineService.create_automation_deadline(
                tenant_id=self.tenant_id,
                entity_type='application',
                entity_id='not-a-uuid',
                action_required='Review application',
                external_reference='runtime-test:invalid-entity',
            )

    def test_create_from_orchestration_returns_normalized_duplicate_result(self):
        context = OwnerActionContext(
            tenant_id=self.tenant_id,
            actor_id=self.user_id,
            external_reference='runtime-test:create-deadline-contract',
            audit_metadata={'automation_run_id': 'run-1', 'rule_id': 'rule-1'},
        )

        first = PipelineDeadlineService.create_from_orchestration(
            context=context,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            due_in_hours=24,
            assigned_to=self.user_id,
            deadline_type='review',
            owner_role='recruiter',
        )
        second = PipelineDeadlineService.create_from_orchestration(
            context=context,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            due_in_hours=24,
            assigned_to=self.user_id,
            deadline_type='review',
            owner_role='recruiter',
        )

        self.assertFalse(first.duplicate)
        self.assertTrue(second.duplicate)
        self.assertEqual(second.execution_status(), 'deduplicated')
        self.assertEqual(second.payload['deadline_type'], 'review')

    def test_escalate_automation_deadline_is_idempotent(self):
        deadline, _ = PipelineDeadlineService.create_automation_deadline(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            due_in_hours=24,
            assigned_to=self.user_id,
            metadata={'deadline_type': 'review'},
            external_reference='runtime-test:deadline-escalate',
        )
        escalated, escalated_created = PipelineDeadlineService.escalate_automation_deadline(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            escalate_to=self.user_id,
            external_reference='runtime-test:deadline-escalate',
        )
        duplicate, duplicate_created = PipelineDeadlineService.escalate_automation_deadline(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            escalate_to=self.user_id,
            external_reference='runtime-test:deadline-escalate',
        )

        self.assertEqual(deadline.id, escalated.id)
        self.assertTrue(escalated_created)
        self.assertFalse(duplicate_created)
        self.assertEqual(duplicate.status, 'escalated')
        self.assertIsNotNone(duplicate.escalated_at)

    def test_assign_automation_deadline_is_idempotent(self):
        deadline, _ = PipelineDeadlineService.create_automation_deadline(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            external_reference='runtime-test:deadline-assign',
        )
        assigned, created = PipelineDeadlineService.assign_automation_deadline(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            assigned_to=self.user_id,
            external_reference='runtime-test:deadline-assign',
        )
        duplicate, duplicate_created = PipelineDeadlineService.assign_automation_deadline(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            assigned_to=self.user_id,
            external_reference='runtime-test:deadline-assign',
        )

        self.assertEqual(deadline.id, assigned.id)
        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(duplicate.assigned_to, self.user_id)

    def test_escalate_from_orchestration_returns_normalized_duplicate_result(self):
        PipelineDeadlineService.create_automation_deadline(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            due_in_hours=24,
            assigned_to=self.user_id,
            metadata={'deadline_type': 'review'},
            external_reference='runtime-test:deadline-escalate-contract',
        )
        context = OwnerActionContext(
            tenant_id=self.tenant_id,
            actor_id=self.user_id,
            external_reference='runtime-test:deadline-escalate-contract',
            audit_metadata={'automation_run_id': 'run-1', 'severity': 'high'},
        )

        first = PipelineDeadlineService.escalate_from_orchestration(
            context=context,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            escalate_to=self.user_id,
            severity='high',
        )
        second = PipelineDeadlineService.escalate_from_orchestration(
            context=context,
            entity_type='application',
            entity_id=self.entity_id,
            action_required='Review shortlisted application',
            escalate_to=self.user_id,
            severity='high',
        )

        self.assertFalse(first.duplicate)
        self.assertTrue(second.duplicate)
        self.assertEqual(second.execution_status(), 'deduplicated')
        self.assertEqual(second.payload['deadline_status'], 'escalated')

    def test_mark_operational_flag_is_idempotent_for_application(self):
        flagged, created = PipelineDeadlineService.mark_operational_flag(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.application.id,
            flag_key='attention_needed',
            flag_value=True,
            metadata={'source': 'test'},
        )
        duplicate, duplicate_created = PipelineDeadlineService.mark_operational_flag(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.application.id,
            flag_key='attention_needed',
            flag_value=True,
            metadata={'source': 'test'},
        )

        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(flagged.id, duplicate.id)
        self.assertTrue(flagged.metadata['operational_flags']['attention_needed']['value'])
