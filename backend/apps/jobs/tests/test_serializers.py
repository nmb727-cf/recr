from django.test import TestCase
from rest_framework.test import APIRequestFactory
from apps.accounts.models import CustomUser
from apps.jobs.models import JobRequisition
from apps.jobs.serializers import JobRequisitionSerializer
import uuid

class JobRequisitionSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.req = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title="Confidential Software Engineer",
            salary_min=100000.00,
            salary_max=200000.00,
            salary_visible=False,
            is_confidential=True,
            budget_code="BUDGET-123",
            description="Secret project details",
            requirements="Secret requirements",
            responsibilities="Secret responsibilities",
            skills_required=["Python", "Go"],
            status='active'
        )

    def test_internal_user_sees_all_fields(self):
        user = CustomUser.objects.create_user(
            email='recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id
        )
        request = self.factory.get('/')
        request.user = user
        
        serializer = JobRequisitionSerializer(self.req, context={'request': request})
        data = serializer.data
        
        # Should see everything
        self.assertEqual(float(data['salary_min']), 100000.00)
        self.assertEqual(data['budget_code'], 'BUDGET-123')
        self.assertEqual(data['description'], 'Secret project details')
        self.assertEqual(data['requirements'], 'Secret requirements')
        self.assertEqual(data['responsibilities'], 'Secret responsibilities')
        self.assertEqual(data['skills_required'], ["Python", "Go"])

    def test_candidate_sees_redacted_fields_when_not_visible_and_confidential(self):
        user = CustomUser.objects.create_user(
            email='candidate@example.com',
            password='testpass123',
            role='candidate'
        )
        request = self.factory.get('/')
        request.user = user
        
        serializer = JobRequisitionSerializer(self.req, context={'request': request})
        data = serializer.data
        
        # Salary should be hidden
        self.assertIsNone(data.get('salary_min'))
        self.assertIsNone(data.get('salary_max'))
        
        # Internal fields should be hidden
        self.assertNotIn('budget_code', data)
        self.assertNotIn('approval_chain', data)
        
        # Confidential info should be redacted
        self.assertEqual(data['description'], "Details for this confidential role will be shared during the interview process.")
        self.assertEqual(data['requirements'], "Redacted for confidentiality.")
        self.assertEqual(data['responsibilities'], "Redacted for confidentiality.")
        self.assertEqual(data['skills_required'], [])

    def test_anonymous_user_sees_redacted_fields(self):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        serializer = JobRequisitionSerializer(self.req, context={'request': request})
        data = serializer.data
        
        self.assertIsNone(data.get('salary_min'))
        self.assertEqual(data['description'], "Details for this confidential role will be shared during the interview process.")
        self.assertNotIn('budget_code', data)
