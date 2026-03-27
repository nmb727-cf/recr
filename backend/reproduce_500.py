import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import CustomUser
from apps.jobs.views import JobRequisitionListView, JobPublicDetailView
from apps.pipeline.views import ApplicationListView
from apps.jobs.models import JobRequisition, JobPosting
from apps.candidates.models import Candidate

def test_submit_application_as_candidate_no_tenant():
    print("Testing Candidate Application Submission (No User Tenant)...")
    factory = APIRequestFactory()
    job_tenant_id = uuid.uuid4()
    
    # Candidate with NO tenant_id
    candidate_user = CustomUser.objects.create_user(
        email=f'candidate_{uuid.uuid4().hex[:6]}@example.com',
        password='testpass123',
        role='candidate',
        tenant_id=None
    )
    
    # Candidate model record
    candidate_model = Candidate.objects.create(
        first_name='Test',
        last_name='Candidate',
        email=candidate_user.email
    )
    
    # Job in a tenant
    job = JobRequisition.objects.create(
        tenant_id=job_tenant_id,
        title='Test Job',
        status='active'
    )
    
    view = ApplicationListView.as_view()
    payload = {
        'requisition_id': str(job.id),
        'candidate_id': str(candidate_model.id),
        'source': 'direct'
    }
    request = factory.post('/api/v1/pipeline/applications/', payload, format='json')
    force_authenticate(request, user=candidate_user)
    
    try:
        response = view(request)
        print(f"Response Code: {response.status_code}")
        if response.status_code >= 400:
            print(f"Response Data: {response.data}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_submit_application_as_candidate_no_tenant()
