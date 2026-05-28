import uuid
from datetime import timedelta

from django.test import TestCase, override_settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate
from apps.interviews.models import (
    Interview,
    InterviewAvailabilityProfile,
    InterviewCalendarConnection,
    InterviewPanelist,
)
from apps.interviews.views import (
    InterviewAvailabilityBlockListView,
    InterviewAvailabilityProfileView,
    InterviewCalendarConnectionView,
    InterviewManualSchedulingView,
    InterviewPanelSlotsView,
    InterviewSchedulingLinkPublicView,
    InterviewSchedulingLinkView,
)
from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application


@override_settings(
    INTERVIEW_SCHEDULING_PUBLIC_RATE_WINDOW_SECONDS=60,
    INTERVIEW_SCHEDULING_PUBLIC_GET_RATE_LIMIT=2,
    INTERVIEW_SCHEDULING_PUBLIC_POST_RATE_LIMIT=2,
)
class InterviewSchedulingEngineTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()

        self.recruiter = CustomUser.objects.create_user(
            email='scheduler@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )
        self.panelist1 = CustomUser.objects.create_user(
            email='panel1@example.com',
            password='testpass123',
            role='interviewer',
            tenant_id=self.tenant_id,
        )
        self.panelist2 = CustomUser.objects.create_user(
            email='panel2@example.com',
            password='testpass123',
            role='interviewer',
            tenant_id=self.tenant_id,
        )

        self.candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Schedule',
            last_name='Candidate',
            email='schedule-candidate@example.com',
            source='company',
        )
        self.job = JobRequisition.objects.create(
            tenant_id=self.tenant_id,
            title='Scheduling Engineer',
            status='active',
        )
        self.application = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            status='shortlisted',
            source='internal',
        )
        self.interview = Interview.objects.create(
            tenant_id=self.tenant_id,
            application_id=self.application.id,
            candidate_id=self.candidate.id,
            requisition_id=self.job.id,
            interview_type='technical',
            interview_round=1,
            duration_minutes=60,
            status='scheduled',
            created_by=self.recruiter.id,
        )

    def test_system_availability_profile_and_blocks_work(self):
        profile_request = self.factory.put(
            '/api/v1/interviews/availability/profile/',
            {
                'mode': 'system',
                'timezone': 'Asia/Kolkata',
            },
            format='json',
        )
        force_authenticate(profile_request, user=self.panelist1)
        profile_response = InterviewAvailabilityProfileView.as_view()(profile_request)
        self.assertEqual(profile_response.status_code, 200)

        block_request = self.factory.post(
            '/api/v1/interviews/availability/blocks/',
            {
                'starts_at': (timezone.now() + timedelta(hours=2)).isoformat(),
                'ends_at': (timezone.now() + timedelta(hours=3)).isoformat(),
                'reason': 'Unavailable for standup',
            },
            format='json',
        )
        force_authenticate(block_request, user=self.panelist1)
        block_response = InterviewAvailabilityBlockListView.as_view()(block_request)
        self.assertEqual(block_response.status_code, 201)

    def test_manual_scheduling_works(self):
        schedule_at = timezone.now() + timedelta(days=1)
        request = self.factory.post(
            '/api/v1/interviews/scheduling/manual/',
            {
                'application_id': str(self.application.id),
                'candidate_id': str(self.candidate.id),
                'requisition_id': str(self.job.id),
                'interview_type': 'panel',
                'title': 'Manual Panel Round',
                'scheduled_at': schedule_at.isoformat(),
                'duration_minutes': 45,
                'panelist_ids': [str(self.panelist1.id), str(self.panelist2.id)],
                'timezone': 'UTC',
            },
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        response = InterviewManualSchedulingView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        interview_id = response.data['data']['interview']['id']
        self.assertTrue(InterviewPanelist.objects.filter(interview_id=interview_id).count() >= 2)

    def test_candidate_self_scheduling_link_and_booking_work(self):
        InterviewPanelist.objects.get_or_create(
            interview_id=self.interview.id,
            interviewer_id=self.panelist1.id,
            defaults={'tenant_id': self.tenant_id, 'role': 'panelist'},
        )

        create_request = self.factory.post(
            f'/api/v1/interviews/{self.interview.id}/scheduling-link/',
            {'timezone': 'Asia/Kolkata', 'expires_in_days': 3},
            format='json',
        )
        force_authenticate(create_request, user=self.recruiter)
        create_response = InterviewSchedulingLinkView.as_view()(create_request, pk=self.interview.id)
        self.assertEqual(create_response.status_code, 201)

        token = create_response.data['data']['link']['token']
        public_get = self.factory.get(f'/api/v1/interviews/scheduling-link/{token}/')
        public_get_response = InterviewSchedulingLinkPublicView.as_view()(public_get, token=token)
        self.assertEqual(public_get_response.status_code, 200)
        public_interview = public_get_response.data['data']['interview']
        self.assertNotIn('candidate_id', public_interview)
        self.assertNotIn('application_id', public_interview)
        self.assertNotIn('requisition_id', public_interview)

        book_request = self.factory.post(
            f'/api/v1/interviews/scheduling-link/{token}/',
            {'slot_start': (timezone.now() + timedelta(days=2)).isoformat(), 'timezone': 'Asia/Kolkata'},
            format='json',
        )
        book_response = InterviewSchedulingLinkPublicView.as_view()(book_request, token=token)
        self.assertEqual(book_response.status_code, 200)
        booked_interview = book_response.data['data']['interview']
        self.assertNotIn('metadata', booked_interview)

    def test_public_scheduling_link_get_rate_limited(self):
        InterviewPanelist.objects.get_or_create(
            interview_id=self.interview.id,
            interviewer_id=self.panelist1.id,
            defaults={'tenant_id': self.tenant_id, 'role': 'panelist'},
        )
        create_request = self.factory.post(
            f'/api/v1/interviews/{self.interview.id}/scheduling-link/',
            {'timezone': 'Asia/Kolkata', 'expires_in_days': 3},
            format='json',
        )
        force_authenticate(create_request, user=self.recruiter)
        create_response = InterviewSchedulingLinkView.as_view()(create_request, pk=self.interview.id)
        token = create_response.data['data']['link']['token']

        req1 = self.factory.get(f'/api/v1/interviews/scheduling-link/{token}/', REMOTE_ADDR='1.2.3.4')
        req2 = self.factory.get(f'/api/v1/interviews/scheduling-link/{token}/', REMOTE_ADDR='1.2.3.4')
        req3 = self.factory.get(f'/api/v1/interviews/scheduling-link/{token}/', REMOTE_ADDR='1.2.3.4')
        self.assertEqual(InterviewSchedulingLinkPublicView.as_view()(req1, token=token).status_code, 200)
        self.assertEqual(InterviewSchedulingLinkPublicView.as_view()(req2, token=token).status_code, 200)
        self.assertEqual(InterviewSchedulingLinkPublicView.as_view()(req3, token=token).status_code, 429)

    def test_calendar_integration_optional_ready(self):
        create_request = self.factory.post(
            '/api/v1/interviews/calendar/connections/',
            {
                'provider': 'google',
                'external_calendar_id': 'primary',
                'account_email': 'panel1@example.com',
                'sync_enabled': False,
            },
            format='json',
        )
        force_authenticate(create_request, user=self.panelist1)
        create_response = InterviewCalendarConnectionView.as_view()(create_request)
        self.assertEqual(create_response.status_code, 201)

        list_request = self.factory.get('/api/v1/interviews/calendar/connections/')
        force_authenticate(list_request, user=self.panelist1)
        list_response = InterviewCalendarConnectionView.as_view()(list_request)
        self.assertEqual(list_response.status_code, 200)
        self.assertGreaterEqual(InterviewCalendarConnection.objects.filter(tenant_id=self.tenant_id).count(), 1)

    def test_panel_availability_and_timezone_handled(self):
        all_day_hours = {
            'mon': {'enabled': True, 'start': '09:00', 'end': '18:00'},
            'tue': {'enabled': True, 'start': '09:00', 'end': '18:00'},
            'wed': {'enabled': True, 'start': '09:00', 'end': '18:00'},
            'thu': {'enabled': True, 'start': '09:00', 'end': '18:00'},
            'fri': {'enabled': True, 'start': '09:00', 'end': '18:00'},
            'sat': {'enabled': True, 'start': '09:00', 'end': '18:00'},
            'sun': {'enabled': True, 'start': '09:00', 'end': '18:00'},
        }
        InterviewAvailabilityProfile.objects.update_or_create(
            tenant_id=self.tenant_id,
            interviewer_id=self.panelist1.id,
            defaults={'timezone': 'Asia/Kolkata', 'working_hours': all_day_hours},
        )
        InterviewAvailabilityProfile.objects.update_or_create(
            tenant_id=self.tenant_id,
            interviewer_id=self.panelist2.id,
            defaults={'timezone': 'Asia/Kolkata', 'working_hours': all_day_hours},
        )

        from_date = timezone.now().date() + timedelta(days=1)
        to_date = from_date + timedelta(days=1)

        request = self.factory.post(
            '/api/v1/interviews/availability/panel-slots/',
            {
                'panelist_ids': [str(self.panelist1.id), str(self.panelist2.id)],
                'from_date': from_date.isoformat(),
                'to_date': to_date.isoformat(),
                'timezone': 'Asia/Kolkata',
                'duration_minutes': 60,
            },
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        response = InterviewPanelSlotsView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        slots = response.data['data']['slots']
        self.assertGreater(len(slots), 0)
        self.assertEqual(slots[0]['timezone'], 'Asia/Kolkata')
