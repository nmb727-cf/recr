import uuid
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import CustomUser
from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application
from apps.analytics.views import RecruitmentAnalyticsView

class RecruitmentAnalyticsTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.dept1_id = uuid.uuid4()
        self.dept2_id = uuid.uuid4()
        
        self.user = CustomUser.objects.create_user(
            email='analyst@example.com',
            password='testpass123',
            role='hr_manager',
            tenant_id=self.tenant_id
        )
        
        # Job in Dept 1
        self.job1 = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title="Dept 1 Job",
            department_id=self.dept1_id,
            status='active'
        )
        # Job in Dept 2
        self.job2 = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title="Dept 2 Job",
            department_id=self.dept2_id,
            status='active'
        )
        
        # 3 applications for Dept 1
        for i in range(3):
            Application.objects.create(
                tenant_id=self.tenant_id,
                candidate_id=uuid.uuid4(),
                requisition_id=self.job1.id,
                status='applied'
            )
            
        # 2 applications for Dept 2
        for i in range(2):
            Application.objects.create(
                tenant_id=self.tenant_id,
                candidate_id=uuid.uuid4(),
                requisition_id=self.job2.id,
                status='applied'
            )

    def test_department_filter_repro(self):
        view = RecruitmentAnalyticsView.as_view()
        
        # Request analytics for Dept 1
        request = self.factory.get(f'/api/v1/analytics/recruitment/?department_id={self.dept1_id}')
        force_authenticate(request, user=self.user)
        
        response = view(request)
        self.assertEqual(response.status_code, 200)
        
        # Currently, this will return 5 (total) instead of 3 (Dept 1)
        data = response.data['data']
        self.assertEqual(data['funnel']['total_applications'], 3)

    def test_no_filter_returns_all(self):
        view = RecruitmentAnalyticsView.as_view()
        request = self.factory.get('/api/v1/analytics/recruitment/')
        force_authenticate(request, user=self.user)
        
        response = view(request)
        self.assertEqual(response.status_code, 200)
        
        data = response.data['data']
        self.assertEqual(data['funnel']['total_applications'], 5)

    def test_rbac_restriction(self):
        # Candidate should NOT have access to recruitment analytics
        candidate = CustomUser.objects.create_user(
            email='candidate_test@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id
        )
        view = RecruitmentAnalyticsView.as_view()
        request = self.factory.get('/api/v1/analytics/recruitment/')
        force_authenticate(request, user=candidate)
        
        response = view(request)
        self.assertEqual(response.status_code, 403)
