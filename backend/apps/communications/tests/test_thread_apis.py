"""
QA Tests: Thread + Message API Endpoints
Uses APIRequestFactory + direct view calls to bypass django-tenants middleware
(same pattern as the rest of this codebase).
"""
import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.communications.models import MessageThread, Message, ThreadParticipant
from apps.communications.communication_service import ThreadService
from apps.communications.views import (
    MessageThreadListView,
    MessageThreadDetailView,
    ThreadMessagesView,
    ThreadMarkReadView,
)

TENANT_A = uuid.UUID('00000000-0000-0000-0000-000000000001')
TENANT_B = uuid.UUID('00000000-0000-0000-0000-000000000002')


def _user(email, tenant_id=TENANT_A, role='recruiter'):
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return CustomUser.objects.create_user(
            email=email, password='testpass123', role=role, tenant_id=tenant_id,
        )


class TestThreadListCreate(TestCase):
    factory = APIRequestFactory()

    def setUp(self):
        self.user1 = _user('thread_user1@test.com', TENANT_A)
        self.user2 = _user('thread_user2@test.com', TENANT_A)

    def test_create_thread_authenticated(self):
        with patch('apps.communications.realtime.RealtimePublisher.publish_message'):
            request = self.factory.post('/messages/threads/', {
                'subject': 'Project X discussion',
                'message': 'Hello team!',
                'participant_user_ids': [str(self.user2.id)],
            }, format='json')
        force_authenticate(request, user=self.user1)
        with patch('apps.communications.realtime.RealtimePublisher.publish_message'):
            response = MessageThreadListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('thread', response.data['data'])
        self.assertIn('message', response.data['data'])

    def test_create_thread_requires_message(self):
        request = self.factory.post('/messages/threads/', {'subject': 'No message'}, format='json')
        force_authenticate(request, user=self.user1)
        response = MessageThreadListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_threads_returns_user_threads(self):
        with patch('apps.communications.realtime.RealtimePublisher.publish_message'):
            ThreadService.create_thread(
                tenant_id=TENANT_A,
                created_by_user_id=self.user1.id,
                participant_user_ids=[self.user1.id],
            )
        request = self.factory.get('/messages/threads/')
        force_authenticate(request, user=self.user1)
        response = MessageThreadListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['data']['threads']), 1)

    def test_unauthenticated_request_rejected(self):
        request = self.factory.get('/messages/threads/')
        response = MessageThreadListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestThreadDetail(TestCase):
    factory = APIRequestFactory()

    def setUp(self):
        self.user1 = _user('detail_user1@test.com', TENANT_A)
        self.user2 = _user('detail_user2@test.com', TENANT_A)
        self.thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=self.user1.id,
            participant_user_ids=[self.user1.id, self.user2.id],
        )

    def test_participant_can_get_thread(self):
        request = self.factory.get(f'/messages/threads/{self.thread.id}/')
        force_authenticate(request, user=self.user1)
        response = MessageThreadDetailView.as_view()(request, pk=self.thread.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['data']['thread']['id']), str(self.thread.id))

    def test_non_participant_cannot_get_thread(self):
        stranger = _user('stranger_detail@test.com', TENANT_A)
        request = self.factory.get(f'/messages/threads/{self.thread.id}/')
        force_authenticate(request, user=stranger)
        response = MessageThreadDetailView.as_view()(request, pk=self.thread.id)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_other_tenant_cannot_access_thread(self):
        other_user = _user('other_tenant_detail@test.com', TENANT_B)
        request = self.factory.get(f'/messages/threads/{self.thread.id}/')
        force_authenticate(request, user=other_user)
        response = MessageThreadDetailView.as_view()(request, pk=self.thread.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestThreadMessages(TestCase):
    factory = APIRequestFactory()

    def setUp(self):
        self.user1 = _user('msg_user1@test.com', TENANT_A)
        self.user2 = _user('msg_user2@test.com', TENANT_A)
        self.thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=self.user1.id,
            participant_user_ids=[self.user1.id, self.user2.id],
        )

    def test_get_messages_for_thread(self):
        with patch('apps.communications.realtime.RealtimePublisher.publish_message'):
            ThreadService.add_message(
                thread_id=self.thread.id,
                requesting_tenant_id=TENANT_A,
                sender_user_id=self.user1.id,
                body='Hello',
            )
        request = self.factory.get(f'/messages/threads/{self.thread.id}/messages/')
        force_authenticate(request, user=self.user1)
        response = ThreadMessagesView.as_view()(request, pk=self.thread.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['data']['messages']), 1)

    def test_post_message_to_thread(self):
        request = self.factory.post(
            f'/messages/threads/{self.thread.id}/messages/',
            {'message': 'New message'},
            format='json',
        )
        force_authenticate(request, user=self.user1)
        with patch('apps.communications.realtime.RealtimePublisher.publish_message'):
            response = ThreadMessagesView.as_view()(request, pk=self.thread.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_participant_cannot_post_message(self):
        stranger = _user('stranger_msg@test.com', TENANT_A)
        request = self.factory.post(
            f'/messages/threads/{self.thread.id}/messages/',
            {'message': 'Unauthorized'},
            format='json',
        )
        force_authenticate(request, user=stranger)
        with patch('apps.communications.realtime.RealtimePublisher.publish_message'):
            response = ThreadMessagesView.as_view()(request, pk=self.thread.id)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_message_body_accessible(self):
        with patch('apps.communications.realtime.RealtimePublisher.publish_message'):
            ThreadService.add_message(
                thread_id=self.thread.id,
                requesting_tenant_id=TENANT_A,
                sender_user_id=self.user1.id,
                body='Specific message content',
            )
        request = self.factory.get(f'/messages/threads/{self.thread.id}/messages/')
        force_authenticate(request, user=self.user1)
        response = ThreadMessagesView.as_view()(request, pk=self.thread.id)
        messages = response.data['data']['messages']
        bodies = [m['body'] for m in messages]
        self.assertIn('Specific message content', bodies)


class TestMarkThreadRead(TestCase):
    factory = APIRequestFactory()

    def setUp(self):
        self.user1 = _user('markread_user1@test.com', TENANT_A)
        self.user2 = _user('markread_user2@test.com', TENANT_A)
        self.thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=self.user1.id,
            participant_user_ids=[self.user1.id, self.user2.id],
        )
        with patch('apps.communications.realtime.RealtimePublisher.publish_message'):
            ThreadService.add_message(
                thread_id=self.thread.id,
                requesting_tenant_id=TENANT_A,
                sender_user_id=self.user1.id,
                body='Unread message',
            )

    def test_mark_thread_read(self):
        request = self.factory.post(f'/messages/threads/{self.thread.id}/mark-read/')
        force_authenticate(request, user=self.user2)
        response = ThreadMarkReadView.as_view()(request, pk=self.thread.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        participant = ThreadParticipant.objects.get(thread=self.thread, user_id=self.user2.id)
        self.assertIsNotNone(participant.last_read_at)
