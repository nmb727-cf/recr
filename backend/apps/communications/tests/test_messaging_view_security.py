import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.communications.messaging_views import (
    EntityThreadView,
    ThreadParticipantAddView,
    ThreadParticipantRemoveView,
)


class MessagingViewSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.candidate = CustomUser.objects.create_user(
            email='msg-candidate@example.com',
            password='testpass123',
            role='candidate',
            tenant_id=self.tenant_id,
        )
        self.recruiter = CustomUser.objects.create_user(
            email='msg-recruiter@example.com',
            password='testpass123',
            role='recruiter',
            tenant_id=self.tenant_id,
        )

    def test_candidate_cannot_create_entity_thread(self):
        request = self.factory.post(
            '/api/v1/communications/messages/threads/entity/',
            {'entity_type': 'candidate', 'entity_id': str(uuid.uuid4())},
            format='json',
        )
        force_authenticate(request, user=self.candidate)
        response = EntityThreadView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_manage_thread_participants(self):
        thread_id = uuid.uuid4()
        participant_id = uuid.uuid4()

        add_request = self.factory.post(
            f'/api/v1/communications/messages/threads/{thread_id}/participants/',
            {'user_id': str(uuid.uuid4())},
            format='json',
        )
        force_authenticate(add_request, user=self.candidate)
        add_response = ThreadParticipantAddView.as_view()(add_request, pk=thread_id)
        self.assertEqual(add_response.status_code, 403)

        remove_request = self.factory.delete(
            f'/api/v1/communications/messages/participants/{participant_id}/'
        )
        force_authenticate(remove_request, user=self.candidate)
        remove_response = ThreadParticipantRemoveView.as_view()(remove_request, participant_id=participant_id)
        self.assertEqual(remove_response.status_code, 403)

    def test_recruiter_is_not_blocked_by_actor_guard(self):
        request = self.factory.post(
            '/api/v1/communications/messages/threads/entity/',
            {'entity_type': 'candidate', 'entity_id': str(uuid.uuid4())},
            format='json',
        )
        force_authenticate(request, user=self.recruiter)
        response = EntityThreadView.as_view()(request)
        self.assertNotEqual(response.status_code, 403)
