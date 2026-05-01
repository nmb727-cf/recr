import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.orchestration_center.models.workflow import Workflow, WorkflowNode, WorkflowEdge
from apps.interviews.models import Interview
from apps.documents.models import OfferLetter
from apps.hdc.models import JoiningCase
from apps.pipeline.models import Application
from apps.workflow_execution.models import WorkflowWaitState, WorkflowTimeline
from apps.workflow_execution.api.views import (
    CompanyAgencySubmissionCallbackView,
    CompanyCandidateResponseCallbackView,
    CompanyCandidateInterviewConfirmCallbackView,
    CompanyCandidateOfferResponseCallbackView,
    CompanyCandidateDocumentUploadedCallbackView,
    CompanyCandidateDocumentSignedCallbackView,
    CompanyHRMSHandoffCallbackView,
    CompanyHRMSHandoffAckCallbackView,
)
from apps.workflow_execution.services.workflow_execution_engine import WorkflowExecutionEngine


def make_waiting_instance(*, tenant_id, wait_node_type='approval', wait_node_config=None):
    workflow = Workflow.objects.create(
        tenant_id=tenant_id,
        name='Company Callback Workflow',
        trigger_event='job_created',
        status='active',
        is_active=True,
    )
    start = WorkflowNode.objects.create(workflow=workflow, node_type='start')
    wait_node = WorkflowNode.objects.create(
        workflow=workflow,
        node_type=wait_node_type,
        config=wait_node_config or {},
    )
    end = WorkflowNode.objects.create(workflow=workflow, node_type='end')
    WorkflowEdge.objects.create(workflow=workflow, source_node=start, target_node=wait_node)
    WorkflowEdge.objects.create(workflow=workflow, source_node=wait_node, target_node=end)

    entity_id = uuid.uuid4()
    instance = WorkflowExecutionEngine.start_workflow_instance(
        tenant_id=tenant_id,
        workflow_id=workflow.id,
        entity_type='job',
        entity_id=entity_id,
    )
    instance.refresh_from_db()
    wait_state = WorkflowWaitState.objects.filter(workflow_instance=instance, status='waiting').first()
    return instance, wait_state


class TestCompanyExternalCallbacks(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()

    def test_agency_submission_callback_resumes_waiting_instance(self):
        instance, wait_state = make_waiting_instance(tenant_id=self.tenant_id)
        self.assertIsNotNone(wait_state)
        instance.wait_reason = 'waiting_client'
        instance.save(update_fields=['wait_reason', 'updated_at'])

        req = self.factory.post(
            '/api/v1/company/external/agency-submission/',
            {
                'tenant_id': str(self.tenant_id),
                'workflow_instance_id': str(instance.id),
                'callback_reference': 'agency-sub-001',
                'payload': {'agency_submission_id': str(uuid.uuid4())},
            },
            format='json',
        )
        response = CompanyAgencySubmissionCallbackView.as_view()(req)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resume_event'], 'client_feedback_received')
        self.assertGreaterEqual(response.data['resumed_count'], 1)

        instance.refresh_from_db()
        self.assertNotEqual(instance.status, 'waiting')
        self.assertTrue(
            WorkflowTimeline.objects.filter(
                workflow_instance=instance,
                event_label='External callback received: agency-submission',
            ).exists()
        )

    def test_candidate_response_callback_maps_accept_to_offer_accepted(self):
        instance, wait_state = make_waiting_instance(tenant_id=self.tenant_id)
        self.assertIsNotNone(wait_state)
        instance.wait_reason = 'waiting_candidate'
        instance.save(update_fields=['wait_reason', 'updated_at'])

        req = self.factory.post(
            '/api/v1/company/external/candidate-response/',
            {
                'tenant_id': str(self.tenant_id),
                'workflow_instance_id': str(instance.id),
                'callback_reference': 'offer-resp-001',
                'payload': {'response': 'accepted'},
            },
            format='json',
        )
        response = CompanyCandidateResponseCallbackView.as_view()(req)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resume_event'], 'offer_accepted')
        self.assertGreaterEqual(response.data['resumed_count'], 1)

    def test_candidate_document_signed_callback_resumes_signature_wait(self):
        instance, wait_state = make_waiting_instance(tenant_id=self.tenant_id, wait_node_type='document')
        self.assertIsNotNone(wait_state)
        instance.wait_reason = 'waiting_signature'
        instance.save(update_fields=['wait_reason', 'updated_at'])

        req = self.factory.post(
            '/api/v1/company/external/candidate-document-signed/',
            {
                'tenant_id': str(self.tenant_id),
                'workflow_instance_id': str(instance.id),
                'callback_reference': 'doc-sign-001',
                'payload': {'document_id': str(uuid.uuid4())},
            },
            format='json',
        )
        response = CompanyCandidateDocumentSignedCallbackView.as_view()(req)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resume_event'], 'document_signed')
        self.assertGreaterEqual(response.data['resumed_count'], 1)

    def test_candidate_interview_confirm_callback_maps_response_variants(self):
        missing_req = self.factory.post(
            '/api/v1/company/external/candidate-interview-confirm/',
            {
                'interview_id': str(uuid.uuid4()),
                'response': 'accepted',
            },
            format='json',
        )
        missing_response = CompanyCandidateInterviewConfirmCallbackView.as_view()(missing_req)
        self.assertEqual(missing_response.status_code, 404)

        interview = Interview.objects.create(
            tenant_id=self.tenant_id,
            application_id=uuid.uuid4(),
            candidate_id=uuid.uuid4(),
            requisition_id=uuid.uuid4(),
            interview_type='technical_interview',
            title='Test Interview',
            status='scheduled',
        )
        interview_instance, _ = make_waiting_instance(tenant_id=self.tenant_id, wait_node_type='wait')
        interview_instance.wait_reason = 'waiting_candidate'
        interview_instance.entity_type = 'interview'
        interview_instance.entity_id = interview.id
        interview_instance.save(update_fields=['wait_reason', 'entity_type', 'entity_id', 'updated_at'])

        req = self.factory.post(
            '/api/v1/company/external/candidate-interview-confirm/',
            {
                'tenant_id': str(self.tenant_id),
                'workflow_instance_id': str(interview_instance.id),
                'interview_id': str(interview.id),
                'response': 'reschedule-request',
                'notes': 'Need evening slot',
            },
            format='json',
        )
        response_obj = CompanyCandidateInterviewConfirmCallbackView.as_view()(req)
        self.assertEqual(response_obj.status_code, 200)
        self.assertEqual(response_obj.data['resume_event'], 'candidate_interview_reschedule_requested')
        self.assertEqual(response_obj.data['response'], 'reschedule-request')
        self.assertGreaterEqual(response_obj.data['resumed_count'], 1)

    def test_callback_requires_scope(self):
        req = self.factory.post(
            '/api/v1/company/external/hrms-handoff-ack/',
            {
                'tenant_id': str(self.tenant_id),
                'callback_reference': 'hrms-ack-001',
                'payload': {'status': 'received'},
            },
            format='json',
        )
        response = CompanyHRMSHandoffAckCallbackView.as_view()(req)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Provide one scope', str(response.data))

    def test_candidate_offer_response_callback_maps_counter(self):
        offer = OfferLetter.objects.create(
            tenant_id=self.tenant_id,
            application_id=uuid.uuid4(),
            candidate_id=uuid.uuid4(),
            title='Backend Engineer Offer',
            offered_salary=1200000,
            currency='INR',
            status='sent',
        )
        instance, wait_state = make_waiting_instance(tenant_id=self.tenant_id, wait_node_type='wait')
        self.assertIsNotNone(wait_state)
        instance.wait_reason = 'waiting_candidate'
        instance.entity_type = 'application'
        instance.entity_id = offer.application_id
        instance.save(update_fields=['wait_reason', 'entity_type', 'entity_id', 'updated_at'])

        req = self.factory.post(
            '/api/v1/company/external/candidate-offer-response/',
            {
                'tenant_id': str(self.tenant_id),
                'workflow_instance_id': str(instance.id),
                'offer_id': str(offer.id),
                'response': 'counter',
                'counter_salary': '1450000.00',
                'notes': 'Can we revise compensation?',
            },
            format='json',
        )
        response = CompanyCandidateOfferResponseCallbackView.as_view()(req)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resume_event'], 'offer_counter_received')
        self.assertEqual(response.data['response'], 'counter')

    def test_candidate_offer_accept_creates_onboarding_case(self):
        application_id = uuid.uuid4()
        candidate_id = uuid.uuid4()
        requisition_id = uuid.uuid4()
        Application.objects.create(
            id=application_id,
            tenant_id=self.tenant_id,
            candidate_id=candidate_id,
            requisition_id=requisition_id,
            status='offer',
        )
        offer = OfferLetter.objects.create(
            tenant_id=self.tenant_id,
            application_id=application_id,
            candidate_id=candidate_id,
            title='Backend Engineer Offer',
            offered_salary=1000000,
            currency='INR',
            status='sent',
        )
        instance, _ = make_waiting_instance(tenant_id=self.tenant_id, wait_node_type='wait')
        instance.wait_reason = 'waiting_candidate'
        instance.entity_type = 'application'
        instance.entity_id = offer.application_id
        instance.save(update_fields=['wait_reason', 'entity_type', 'entity_id', 'updated_at'])

        req = self.factory.post(
            '/api/v1/company/external/candidate-offer-response/',
            {
                'tenant_id': str(self.tenant_id),
                'workflow_instance_id': str(instance.id),
                'offer_id': str(offer.id),
                'response': 'accepted',
            },
            format='json',
        )
        response = CompanyCandidateOfferResponseCallbackView.as_view()(req)
        self.assertEqual(response.status_code, 200)

        onboarding = JoiningCase.objects.filter(
            tenant_id=self.tenant_id,
            application_id=offer.application_id,
        ).first()
        self.assertIsNotNone(onboarding)
        self.assertEqual(onboarding.status, 'pending')

    def test_candidate_document_uploaded_callback_updates_onboarding(self):
        onboarding = JoiningCase.objects.create(
            tenant_id=self.tenant_id,
            application_id=uuid.uuid4(),
            status='documents_pending',
            metadata={'checklist': [{'task_name': 'documents received', 'status': 'pending'}]},
        )
        instance, _ = make_waiting_instance(tenant_id=self.tenant_id, wait_node_type='document')
        instance.wait_reason = 'waiting_signature'
        instance.entity_type = 'application'
        instance.entity_id = onboarding.application_id
        instance.save(update_fields=['wait_reason', 'entity_type', 'entity_id', 'updated_at'])

        req = self.factory.post(
            '/api/v1/company/external/candidate-document-uploaded/',
            {
                'tenant_id': str(self.tenant_id),
                'workflow_instance_id': str(instance.id),
                'onboarding_id': str(onboarding.id),
                'document_type': 'ID proof',
                'document_status': 'uploaded',
            },
            format='json',
        )
        response = CompanyCandidateDocumentUploadedCallbackView.as_view()(req)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resume_event'], 'document_signed')

        onboarding.refresh_from_db()
        self.assertEqual(onboarding.status, 'in_progress')
        self.assertIn('ID proof', onboarding.metadata.get('documents', {}))

    def test_hrms_handoff_callback_marks_case_handed_off(self):
        onboarding = JoiningCase.objects.create(
            tenant_id=self.tenant_id,
            application_id=uuid.uuid4(),
            status='completed',
        )
        instance, _ = make_waiting_instance(tenant_id=self.tenant_id, wait_node_type='wait')
        instance.wait_reason = 'waiting_other'
        instance.entity_type = 'application'
        instance.entity_id = onboarding.application_id
        instance.save(update_fields=['wait_reason', 'entity_type', 'entity_id', 'updated_at'])

        req = self.factory.post(
            '/api/v1/company/external/hrms-handoff/',
            {
                'tenant_id': str(self.tenant_id),
                'workflow_instance_id': str(instance.id),
                'onboarding_id': str(onboarding.id),
                'status': 'acknowledged',
            },
            format='json',
        )
        response = CompanyHRMSHandoffCallbackView.as_view()(req)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resume_event'], 'hrms_handoff_acknowledged')
        onboarding.refresh_from_db()
        self.assertEqual(onboarding.status, 'handed_off')
