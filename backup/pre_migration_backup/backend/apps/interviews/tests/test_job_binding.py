from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import CustomUser
from apps.interviews.models import InterviewPackage, InterviewPackageBinding
from apps.interviews.views import JobInterviewBindingView
import uuid
import json

class JobInterviewBindingTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = str(uuid.uuid4())
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_id,
        )

    def test_create_binding(self):
        job_id = str(uuid.uuid4())
        package = InterviewPackage.objects.create(
            tenant_id=self.tenant_id,
            title="Standard Engineering Process",
            rounds=[
                {"name": "Technical Round 1", "type": "technical", "threshold_score": 70, "auto_pass_enabled": True},
            ]
        )
        
        request = self.factory.post(
            f'/api/v1/interviews/jobs/requisitions/{job_id}/interview-binding/',
            {'package_id': str(package.id)},
            format='json'
        )
        force_authenticate(request, user=self.user)
        view = JobInterviewBindingView.as_view()
        response = view(request, requisition_id=job_id)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['binding']['package_title'], package.title)
        self.assertEqual(len(response.data['data']['binding']['effective_rounds']), 1)

    def test_override_rounds(self):
        job_id = str(uuid.uuid4())
        package = InterviewPackage.objects.create(
            tenant_id=self.tenant_id,
            title="Standard Process",
            rounds=[{"name": "Round 1", "type": "technical", "threshold_score": 70}]
        )
        
        overridden_rounds = [
            {"name": "Harder Round", "type": "technical", "threshold_score": 90}
        ]
        request = self.factory.post(
            f'/api/v1/interviews/jobs/requisitions/{job_id}/interview-binding/',
            {
                'package_id': str(package.id),
                'rounds_override': overridden_rounds
            },
            format='json'
        )
        force_authenticate(request, user=self.user)
        view = JobInterviewBindingView.as_view()
        response = view(request, requisition_id=job_id)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['binding']['effective_rounds'][0]['threshold_score'], 90)
        self.assertEqual(response.data['data']['binding']['effective_rounds'][0]['name'], "Harder Round")

    def test_update_automation_settings(self):
        job_id = str(uuid.uuid4())
        package = InterviewPackage.objects.create(
            tenant_id=self.tenant_id,
            title="Process"
        )
        binding = InterviewPackageBinding.objects.create(
            tenant_id=self.tenant_id,
            job_id=job_id,
            package=package,
            automation_enabled=True
        )
        
        request = self.factory.put(
            f'/api/v1/interviews/jobs/requisitions/{job_id}/interview-binding/',
            {'automation_enabled': False},
            format='json'
        )
        force_authenticate(request, user=self.user)
        view = JobInterviewBindingView.as_view()
        response = view(request, requisition_id=job_id)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['data']['binding']['automation_enabled'])
        
        binding.refresh_from_db()
        self.assertFalse(binding.automation_enabled)
