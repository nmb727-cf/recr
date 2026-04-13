import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate, CandidateEngagement
from apps.jobs.models import JobRequisition
from apps.candidates.views import CandidateListView, CandidateEngagementListView

def test_duplicate_notifications():
    print("Testing Duplicate Notification Status Codes (Expected 409)...")
    factory = APIRequestFactory()
    tenant_id = uuid.uuid4()
    user = CustomUser.objects.create_user(
        email=f'recruiter_{uuid.uuid4().hex[:6]}@example.com',
        password='testpass123',
        role='recruiter',
        tenant_id=tenant_id
    )
    
    # 1. Candidate Database Duplicate
    view_list = CandidateListView.as_view()
    payload = {
        'first_name': 'Notify',
        'last_name': 'Test',
        'email': 'notify@example.com'
    }
    # Create
    req1 = factory.post('/api/v1/candidates/', payload, format='json')
    force_authenticate(req1, user=user)
    view_list(req1)
    
    # Duplicate
    req2 = factory.post('/api/v1/candidates/', payload, format='json')
    force_authenticate(req2, user=user)
    response = view_list(req2)
    print(f"Candidate Database Duplicate Status: {response.status_code} (Expected 409)")

    # 2. Job Engagement Duplicate
    job = JobRequisition.objects.create(tenant_id=tenant_id, title='Job', status='active')
    cand = Candidate.objects.create(tenant_id=tenant_id, first_name='C', last_name='D', email='cd@ex.com')
    view_eng = CandidateEngagementListView.as_view()
    payload_eng = {'job': str(job.id), 'stage': 'submitted'}
    
    # Create
    req3 = factory.post(f'/api/v1/candidates/{cand.id}/engagements/', payload_eng, format='json')
    force_authenticate(req3, user=user)
    view_eng(req3, candidate_id=str(cand.id))
    
    # Duplicate
    req4 = factory.post(f'/api/v1/candidates/{cand.id}/engagements/', payload_eng, format='json')
    force_authenticate(req4, user=user)
    response_eng = view_eng(req4, candidate_id=str(cand.id))
    print(f"Job Engagement Duplicate Status: {response_eng.status_code} (Expected 409)")

    # 3. General Pool Duplicate (No stage change)
    payload_gen = {'stage': 'new_lead'}
    # Create
    req5 = factory.post(f'/api/v1/candidates/{cand.id}/engagements/', payload_gen, format='json')
    force_authenticate(req5, user=user)
    view_eng(req5, candidate_id=str(cand.id))
    
    # Duplicate
    req6 = factory.post(f'/api/v1/candidates/{cand.id}/engagements/', payload_gen, format='json')
    force_authenticate(req6, user=user)
    response_gen = view_eng(req6, candidate_id=str(cand.id))
    print(f"General Pool Duplicate Status: {response_gen.status_code} (Expected 409)")

if __name__ == "__main__":
    test_duplicate_notifications()
