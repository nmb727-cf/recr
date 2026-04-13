import uuid
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate, CandidateTenantRight
from apps.jobs.models import JobRequisition, JobStage
from apps.pipeline.models import Application
from apps.pipeline.views import ApplicationDetailView, ApplicationMoveStageView
from django.utils import timezone
from datetime import timedelta
from rest_framework import status

class ProtectionBypassTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.agency_tenant_id = uuid.uuid4()
        
        self.user = CustomUser.objects.create_user(
            email='recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id
        )
        
        # Candidate is protected only for 'Allowed Job'
        self.candidate = Candidate.objects.create(
            first_name="Protected",
            last_name="Candidate",
            email="protected@example.com",
            tenant_id=self.tenant_id
        )
        
        self.allowed_job = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title="Allowed Job",
            status='active'
        )
        self.disallowed_job = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title="Disallowed Job",
            status='active'
        )

        self.right = CandidateTenantRight.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            source_tenant_id=self.agency_tenant_id,
            target_tenant_id=self.tenant_id,
            relationship_type='protected',
            status='active',
            protected_until=timezone.now() + timedelta(days=30),
            retention_scope='job_only',
            allowed_job_ids=[str(self.allowed_job.id)]
        )

    def test_move_stage_bypass_protection_repro(self):
        # Create application for disallowed job
        stage = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=self.disallowed_job.id,
            name="Stage 1",
            stage_order=1,
            stage_type='screening'
        )
        target_stage = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=self.disallowed_job.id,
            name="Stage 2",
            stage_order=2,
            stage_type='interview'
        )
        
        app = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            requisition_id=self.disallowed_job.id,
            current_stage_id=stage.id,
            status='screening'
        )
        
        view = ApplicationMoveStageView.as_view()
        payload = {
            'stage_id': str(target_stage.id),
            'note': 'Attempting move on unprotected job context'
        }
        request = self.factory.post(f'/api/v1/pipeline/applications/{app.id}/move/', payload, format='json')
        force_authenticate(request, user=self.user)
        
        response = view(request, pk=app.id)
        
        # This SHOULD be forbidden because the candidate is protected for 'Allowed Job' ONLY.
        # But currently it succeeds.
        self.assertEqual(response.status_code, 403)

    def test_detail_put_bypass_protection_repro(self):
        app = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            requisition_id=self.disallowed_job.id,
            status='screening'
        )
        
        view = ApplicationDetailView.as_view()
        payload = {
            'status': 'interview',
            'note': 'Attempting status change via PUT'
        }
        request = self.factory.put(f'/api/v1/pipeline/applications/{app.id}/', payload, format='json')
        force_authenticate(request, user=self.user)
        
        response = view(request, pk=app.id)
        
        # This SHOULD be forbidden.
        self.assertEqual(response.status_code, 403)
