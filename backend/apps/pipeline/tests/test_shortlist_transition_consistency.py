import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.jobs.models import JobRequisition, JobStage
from apps.pipeline.models import Application, ApplicationStageHistory
from apps.pipeline.views import ApplicationShortlistView


class ShortlistTransitionConsistencyTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.user = CustomUser.objects.create_user(
            email='shortlist-owner@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_id,
        )
        self.candidate = Candidate.objects.create(
            first_name='Short',
            last_name='List',
            email='short.list@example.com',
            tenant_id=self.tenant_id,
        )
        self.job = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Shortlist Consistency Job',
            status='active',
            job_owner_id=self.user.id,
            hiring_manager_id=self.user.id,
            recruiter_id=self.user.id,
            is_workflow_controlled=False,
        )
        self.screening_stage = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
            name='Screening',
            stage_order=1,
            stage_type='screening',
            decision_authority='any',
        )
        self.application = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            current_stage_id=self.screening_stage.id,
            status='screening',
            created_by=self.user.id,
        )

    def test_shortlist_uses_shortlisted_stage_when_configured(self):
        shortlist_stage = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
            name='Shortlisted',
            stage_order=2,
            stage_type='shortlisted',
            decision_authority='any',
        )

        request = self.factory.post(
            f'/api/v1/pipeline/applications/{self.application.id}/shortlist/',
            {'notes': 'shortlist via explicit stage'},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = ApplicationShortlistView.as_view()(request, pk=self.application.id)
        self.assertEqual(response.status_code, 200)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'shortlisted')
        self.assertEqual(self.application.current_stage_id, shortlist_stage.id)

        history = ApplicationStageHistory.objects.filter(application_id=self.application.id).order_by('-moved_at').first()
        self.assertIsNotNone(history)
        self.assertEqual(history.to_status, 'shortlisted')
        self.assertEqual(history.to_stage_id, shortlist_stage.id)

    def test_shortlist_falls_back_to_legacy_status_when_stage_missing(self):
        request = self.factory.post(
            f'/api/v1/pipeline/applications/{self.application.id}/shortlist/',
            {'notes': 'legacy shortlist path'},
            format='json',
        )
        force_authenticate(request, user=self.user)

        response = ApplicationShortlistView.as_view()(request, pk=self.application.id)
        self.assertEqual(response.status_code, 200)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'shortlisted')
        self.assertEqual(self.application.current_stage_id, self.screening_stage.id)

        history = ApplicationStageHistory.objects.filter(application_id=self.application.id).order_by('-moved_at').first()
        self.assertIsNotNone(history)
        self.assertEqual(history.to_status, 'shortlisted')
        self.assertEqual(history.to_stage_id, self.screening_stage.id)
