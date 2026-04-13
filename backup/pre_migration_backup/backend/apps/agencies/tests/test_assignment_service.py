import uuid

from django.test import TestCase

from apps.agencies.models import AgencyClientRelationship, AgencyJobAssignment
from apps.agencies.services import AgencyAssignmentService, AgencyOperationalFlagService
from shared.owner_contracts import OwnerActionContext


class AgencyAssignmentServiceTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.other_tenant_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        self.requisition_id = uuid.uuid4()
        self.agency_tenant_id = uuid.uuid4()
        AgencyClientRelationship.objects.create(
            tenant_id=self.tenant_id,
            agency_tenant_id=self.agency_tenant_id,
            company_tenant_id=self.tenant_id,
            status='active',
            created_by=self.user_id,
        )

    def test_assign_job_to_agency_is_idempotent_for_same_active_assignment(self):
        assignment, created = AgencyAssignmentService.assign_job_to_agency(
            tenant_id=self.tenant_id,
            requisition_id=self.requisition_id,
            agency_tenant_id=self.agency_tenant_id,
            assigned_by=self.user_id,
            notes='Priority role',
            external_reference='agency-assignment-dedupe',
        )
        duplicate, duplicate_created = AgencyAssignmentService.assign_job_to_agency(
            tenant_id=self.tenant_id,
            requisition_id=self.requisition_id,
            agency_tenant_id=self.agency_tenant_id,
            assigned_by=self.user_id,
            notes='Priority role',
            external_reference='agency-assignment-dedupe',
        )

        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(assignment.id, duplicate.id)
        self.assertEqual(
            AgencyJobAssignment.objects.filter(
                tenant_id=self.tenant_id,
                requisition_id=self.requisition_id,
                agency_tenant_id=self.agency_tenant_id,
            ).count(),
            1,
        )

    def test_assign_job_to_agency_preserves_tenant_isolation(self):
        with self.assertRaisesMessage(ValueError, 'Active agency relationship not found for assignment.'):
            AgencyAssignmentService.assign_job_to_agency(
                tenant_id=self.other_tenant_id,
                requisition_id=self.requisition_id,
                agency_tenant_id=self.agency_tenant_id,
                assigned_by=self.user_id,
            )

    def test_mark_operational_flag_is_idempotent_for_job_assignment(self):
        assignment, _ = AgencyAssignmentService.assign_job_to_agency(
            tenant_id=self.tenant_id,
            requisition_id=self.requisition_id,
            agency_tenant_id=self.agency_tenant_id,
            assigned_by=self.user_id,
            external_reference='agency-assignment-for-flag',
        )
        flagged, created = AgencyOperationalFlagService.mark_operational_flag(
            tenant_id=self.tenant_id,
            entity_type='job_assignment',
            entity_id=assignment.id,
            flag_key='attention_needed',
            flag_value=True,
            external_reference='agency-flag-dedupe',
        )
        duplicate, duplicate_created = AgencyOperationalFlagService.mark_operational_flag(
            tenant_id=self.tenant_id,
            entity_type='job_assignment',
            entity_id=assignment.id,
            flag_key='attention_needed',
            flag_value=True,
            external_reference='agency-flag-dedupe',
        )

        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(flagged.id, duplicate.id)
        self.assertTrue(flagged.metadata['operational_flags']['attention_needed']['value'])

    def test_mark_operational_flag_preserves_tenant_isolation(self):
        assignment, _ = AgencyAssignmentService.assign_job_to_agency(
            tenant_id=self.tenant_id,
            requisition_id=self.requisition_id,
            agency_tenant_id=self.agency_tenant_id,
            assigned_by=self.user_id,
            external_reference='agency-assignment-for-isolation-flag',
        )
        with self.assertRaisesMessage(ValueError, 'Agency job assignment not found for flagging.'):
            AgencyOperationalFlagService.mark_operational_flag(
                tenant_id=self.other_tenant_id,
                entity_type='job_assignment',
                entity_id=assignment.id,
                flag_key='review_required',
                flag_value=True,
            )

    def test_assign_from_orchestration_returns_normalized_duplicate_result(self):
        context = OwnerActionContext(
            tenant_id=self.tenant_id,
            actor_id=self.user_id,
            external_reference='agency-contract-dedupe',
            audit_metadata={'automation_run_id': 'run-1', 'assignment_reason': 'automation_rule'},
        )

        first = AgencyAssignmentService.assign_from_orchestration(
            context=context,
            requisition_id=self.requisition_id,
            agency_tenant_id=self.agency_tenant_id,
            notes='Priority role',
        )
        second = AgencyAssignmentService.assign_from_orchestration(
            context=context,
            requisition_id=self.requisition_id,
            agency_tenant_id=self.agency_tenant_id,
            notes='Priority role',
        )

        self.assertFalse(first.duplicate)
        self.assertTrue(second.duplicate)
        self.assertEqual(second.execution_status(), 'deduplicated')
        self.assertEqual(second.payload['requisition_id'], str(self.requisition_id))
