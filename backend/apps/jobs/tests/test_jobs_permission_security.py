import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.jobs.models import JobRequisition, JobPosting, JobDescriptionTemplate, JobStage
from apps.jobs.views import (
    JobRequisitionListView,
    JobRequisitionDetailView,
    JobRequisitionPublishView,
    JobPostingPauseView,
    JDTemplateListView,
    JobStageReorderView,
)


class JobsPermissionSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.recruiter = CustomUser.objects.create_user(
            email='jobs-perm-recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )

    def test_recruiter_without_create_permission_cannot_create_requisition(self):
        request = self.factory.post(
            '/api/v1/jobs/requisitions/',
            {'title': 'Permission Guard Test Job', 'headcount': 1},
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        with patch('apps.jobs.views.user_has_permission', return_value=False):
            response = JobRequisitionListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_recruiter_without_edit_permission_cannot_update_requisition(self):
        req = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Editable Job',
            created_by=self.recruiter.id,
            status='draft',
        )
        request = self.factory.put(
            f'/api/v1/jobs/requisitions/{req.id}/',
            {'title': 'Updated Title'},
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        with patch('apps.jobs.views.user_has_permission', return_value=False):
            response = JobRequisitionDetailView.as_view()(request, pk=req.id)
        self.assertEqual(response.status_code, 403)

    def test_recruiter_without_approve_permission_cannot_publish_requisition(self):
        req = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Publishable Job',
            description='Ready description',
            headcount=1,
            hiring_manager_id=uuid.uuid4(),
            recruiter_id=self.recruiter.id,
            created_by=self.recruiter.id,
            status='draft',
        )
        request = self.factory.post(f'/api/v1/jobs/requisitions/{req.id}/publish/', {}, format='json')
        force_authenticate(request, user=self.recruiter)
        with patch('apps.jobs.views.user_has_permission', return_value=False):
            response = JobRequisitionPublishView.as_view()(request, pk=req.id)
        self.assertEqual(response.status_code, 403)

    def test_recruiter_without_edit_permission_cannot_pause_posting(self):
        req = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Posting Parent Job',
            created_by=self.recruiter.id,
            status='active',
        )
        posting = JobPosting.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=req.id,
            title='Posting',
            slug='posting-security-test',
            is_active=True,
            created_by=self.recruiter.id,
        )
        request = self.factory.post(f'/api/v1/jobs/postings/{posting.id}/pause/', {}, format='json')
        force_authenticate(request, user=self.recruiter)
        with patch('apps.jobs.views.user_has_permission', return_value=False):
            response = JobPostingPauseView.as_view()(request, pk=posting.id)
        self.assertEqual(response.status_code, 403)

    def test_recruiter_without_create_permission_cannot_create_jd_template(self):
        request = self.factory.post(
            '/api/v1/jobs/templates/',
            {'name': 'Template A', 'description': 'desc'},
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        with patch('apps.jobs.views.user_has_permission', return_value=False):
            response = JDTemplateListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_recruiter_without_edit_permission_cannot_reorder_stages(self):
        req = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Stage Reorder Job',
            created_by=self.recruiter.id,
            status='draft',
        )
        stage1 = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=req.id,
            name='Applied',
            stage_order=1,
            stage_type='screening',
            created_by=self.recruiter.id,
        )
        stage2 = JobStage.objects.create(
            tenant_id=self.tenant_id,
            requisition_id=req.id,
            name='Screening',
            stage_order=2,
            stage_type='screening',
            created_by=self.recruiter.id,
        )
        request = self.factory.post(
            f'/api/v1/jobs/requisitions/{req.id}/stages/reorder/',
            {'stage_ids': [str(stage2.id), str(stage1.id)]},
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        with patch('apps.jobs.views.user_has_permission', return_value=False):
            response = JobStageReorderView.as_view()(request, requisition_id=req.id)
        self.assertEqual(response.status_code, 403)
