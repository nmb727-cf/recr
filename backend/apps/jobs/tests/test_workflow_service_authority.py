import uuid

from django.test import TestCase

from apps.accounts.models import CustomUser
from apps.jobs.models import JobRequisition, JobStage
from apps.jobs.workflow_service import JobWorkflowService
from apps.pipeline.models import Application


class WorkflowServiceAuthorityTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.owner = CustomUser.objects.create_user(
            email='owner-workflow@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_id,
        )
        self.recruiter = CustomUser.objects.create_user(
            email='recruiter-workflow@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )
        self.hm = CustomUser.objects.create_user(
            email='hm-workflow@example.com',
            password='testpass123',
            role='hiring_manager',
            tenant_id=self.tenant_id,
        )
        self.other_user = CustomUser.objects.create_user(
            email='other-workflow@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )

        self.requisition = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Authority Check Job',
            status='active',
            job_owner_id=self.owner.id,
            recruiter_id=self.recruiter.id,
            hiring_manager_id=self.hm.id,
            is_workflow_controlled=True,
        )
        self.stage1 = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=self.requisition.id,
            name='Screening',
            stage_order=1,
            stage_type='screening',
            decision_authority='any',
        )
        self.recruiter_stage = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=self.requisition.id,
            name='Recruiter Decision',
            stage_order=2,
            stage_type='interview',
            decision_authority='recruiter',
        )
        self.hm_stage = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=self.requisition.id,
            name='HM Decision',
            stage_order=3,
            stage_type='offer',
            decision_authority='hiring_manager',
        )
        self.app = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=uuid.uuid4(),
            requisition_id=self.requisition.id,
            current_stage_id=self.stage1.id,
            status='screening',
        )

    def test_non_authorized_user_blocked_for_recruiter_authority_stage(self):
        allowed, msg = JobWorkflowService.can_move_to_stage(
            self.requisition,
            self.app,
            self.recruiter_stage,
            user=self.other_user,
        )
        self.assertFalse(allowed)
        self.assertIn('Decision Authority restricted', msg)

    def test_authorized_recruiter_allowed_for_recruiter_authority_stage(self):
        allowed, msg = JobWorkflowService.can_move_to_stage(
            self.requisition,
            self.app,
            self.recruiter_stage,
            user=self.recruiter,
        )
        self.assertTrue(allowed)
        self.assertEqual(msg, '')

    def test_non_authorized_user_blocked_for_hiring_manager_authority_stage(self):
        app_at_recruiter_stage = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=uuid.uuid4(),
            requisition_id=self.requisition.id,
            current_stage_id=self.recruiter_stage.id,
            status='interview',
        )
        allowed, msg = JobWorkflowService.can_move_to_stage(
            self.requisition,
            app_at_recruiter_stage,
            self.hm_stage,
            user=self.other_user,
        )
        self.assertFalse(allowed)
        self.assertIn('Decision Authority restricted', msg)

