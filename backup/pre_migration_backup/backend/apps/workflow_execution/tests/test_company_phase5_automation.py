import uuid

from django.test import TestCase

from apps.documents.models import OfferLetter
from apps.documents.views import _create_offer_approval_human_task
from apps.pipeline.models import Application
from apps.workflow_execution.models import WorkflowHumanTask, WorkflowInstance
from apps.workflow_execution.signals import on_candidate_applied


class TestCompanyPhase5Automation(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.application = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=uuid.uuid4(),
            requisition_id=uuid.uuid4(),
            status='applied',
        )
        self.instance = WorkflowInstance.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=uuid.uuid4(),
            entity_type='application',
            entity_id=self.application.id,
            status='running',
            context_data={},
        )

    def test_candidate_added_creates_recruiter_review_task(self):
        on_candidate_applied(sender=self.__class__, application=self.application)
        self.assertTrue(
            WorkflowHumanTask.objects.filter(
                workflow_instance=self.instance,
                title='Recruiter review pending',
                task_type='review',
            ).exists()
        )

    def test_offer_approval_pending_creates_human_task(self):
        offer = OfferLetter.objects.create(
            tenant_id=self.tenant_id,
            application_id=self.application.id,
            candidate_id=self.application.candidate_id,
            title='Offer Letter - Senior Engineer',
            status='approval_pending',
        )
        _create_offer_approval_human_task(offer=offer)
        self.assertTrue(
            WorkflowHumanTask.objects.filter(
                workflow_instance=self.instance,
                task_type='approval',
                title__icontains='Offer approval pending',
            ).exists()
        )
