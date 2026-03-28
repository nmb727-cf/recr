import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.jobs.models import JobRequisition, JobStage
from apps.pipeline.models import Application
from apps.pipeline.views import (
    ApplicationDetailView,
    ApplicationMoveStageView,
    validate_application_move,
)


class PostSubmissionStageOwnershipTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()

        self.owner_user = CustomUser.objects.create_user(
            email='owner@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )
        self.recruiter_user = CustomUser.objects.create_user(
            email='recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )
        self.agency_user = CustomUser.objects.create_user(
            email='agency@example.com',
            password='testpass123',
            role='agency_recruiter',
            tenant_id=self.tenant_id,
        )
        self.threshold_automation_user = CustomUser.objects.create_user(
            email='threshold-automation@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
            metadata={'actor_mode': 'threshold_automation'},
        )

        self.candidate = Candidate.objects.create(
            first_name='Stage',
            last_name='Candidate',
            email='stage-candidate@example.com',
            tenant_id=self.tenant_id,
        )

        self.job = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Backend Engineer',
            status='active',
            created_by=self.owner_user.id,
        )

        self.screening_stage = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
            name='Under Review',
            stage_order=1,
            stage_type='screening',
        )
        self.interview_stage = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=self.job.id,
            name='Interview',
            stage_order=2,
            stage_type='interview',
        )

        self.application = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            current_stage_id=self.screening_stage.id,
            status='screening',
            created_by=self.owner_user.id,
        )

    @patch('apps.pipeline.views.check_protected_action', return_value=(True, '', {}))
    def test_agency_user_cannot_move_stage(self, _mock_protection):
        request = self.factory.post(
            f'/api/v1/pipeline/applications/{self.application.id}/move-stage/',
            {'stage_id': str(self.interview_stage.id), 'note': 'manual move'},
            format='json',
        )
        force_authenticate(request, user=self.agency_user)

        response = ApplicationMoveStageView.as_view()(request, pk=self.application.id)
        self.assertEqual(response.status_code, 403)

    @patch('apps.pipeline.views.check_protected_action', return_value=(True, '', {}))
    def test_recruiter_non_owner_cannot_move_stage(self, _mock_protection):
        request = self.factory.post(
            f'/api/v1/pipeline/applications/{self.application.id}/move-stage/',
            {'stage_id': str(self.interview_stage.id), 'note': 'manual move'},
            format='json',
        )
        force_authenticate(request, user=self.recruiter_user)

        response = ApplicationMoveStageView.as_view()(request, pk=self.application.id)
        self.assertEqual(response.status_code, 403)

    @patch('apps.pipeline.views.check_protected_action', return_value=(True, '', {}))
    def test_job_owner_can_move_stage(self, _mock_protection):
        request = self.factory.post(
            f'/api/v1/pipeline/applications/{self.application.id}/move-stage/',
            {'stage_id': str(self.interview_stage.id), 'note': 'owner move'},
            format='json',
        )
        force_authenticate(request, user=self.owner_user)

        response = ApplicationMoveStageView.as_view()(request, pk=self.application.id)
        self.assertEqual(response.status_code, 200)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'interview')
        self.assertEqual(self.application.current_stage_id, self.interview_stage.id)

    def test_automation_without_user_is_allowed(self):
        is_valid, error_msg = validate_application_move(
            self.application,
            self.interview_stage,
            reason='automated threshold move',
            user=None,
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_approved_threshold_automation_user_is_allowed(self):
        is_valid, error_msg = validate_application_move(
            self.application,
            self.interview_stage,
            reason='approved threshold move',
            user=self.threshold_automation_user,
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    @patch('apps.pipeline.views.check_protected_action', return_value=(True, '', {}))
    def test_api_restriction_enforced_on_application_put(self, _mock_protection):
        request = self.factory.put(
            f'/api/v1/pipeline/applications/{self.application.id}/',
            {'status': 'interview', 'note': 'put status move'},
            format='json',
        )
        force_authenticate(request, user=self.recruiter_user)

        response = ApplicationDetailView.as_view()(request, pk=self.application.id)
        self.assertEqual(response.status_code, 403)
