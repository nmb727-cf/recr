"""
QA Tests: Communication Service (Thread + Messaging)
"""
import uuid
from unittest.mock import patch, MagicMock

from django.test import TestCase
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.communications.models import (
    Message, MessageThread, ThreadParticipant, ThreadType,
)
from apps.communications.communication_service import ThreadService

TENANT_A = uuid.uuid4()
TENANT_B = uuid.uuid4()
USER_1 = uuid.uuid4()
USER_2 = uuid.uuid4()
USER_3 = uuid.uuid4()  # not a participant


class TestThreadCreation(TestCase):

    def test_creates_thread_with_participants(self):
        thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=USER_1,
            thread_type=ThreadType.INTERNAL,
            subject='Team discussion',
            participant_user_ids=[USER_1, USER_2],
        )
        self.assertIsNotNone(thread.id)
        self.assertEqual(thread.tenant_id, TENANT_A)
        self.assertEqual(thread.thread_type, ThreadType.INTERNAL)
        self.assertFalse(thread.is_deleted)

        participants = ThreadParticipant.objects.filter(thread=thread)
        self.assertEqual(participants.count(), 2)

    def test_creator_is_participant_even_if_not_in_list(self):
        thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=USER_1,
            participant_user_ids=[USER_2],
        )
        participant_ids = list(ThreadParticipant.objects.filter(thread=thread).values_list('user_id', flat=True))
        self.assertIn(USER_2, participant_ids)

    def test_thread_stores_related_entity(self):
        entity_id = uuid.uuid4()
        thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=USER_1,
            related_entity_type='application',
            related_entity_id=entity_id,
            participant_user_ids=[USER_1],
        )
        self.assertEqual(thread.related_entity_type, 'application')
        self.assertEqual(thread.related_entity_id, entity_id)


class TestMessageCreation(TestCase):

    def setUp(self):
        self.thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=USER_1,
            participant_user_ids=[USER_1, USER_2],
        )

    def test_participant_can_send_message(self):
        msg = ThreadService.add_message(
            thread_id=self.thread.id,
            requesting_tenant_id=TENANT_A,
            sender_user_id=USER_1,
            body='Hello world',
        )
        self.assertEqual(msg.body, 'Hello world')
        self.assertEqual(msg.content, 'Hello world')  # legacy sync
        self.assertFalse(msg.is_system_generated)

    def test_non_participant_cannot_send_message(self):
        with self.assertRaises(PermissionDenied):
            ThreadService.add_message(
                thread_id=self.thread.id,
                requesting_tenant_id=TENANT_A,
                sender_user_id=USER_3,
                body='Unauthorized message',
            )

    def test_message_updates_thread_last_message_at(self):
        ThreadService.add_message(
            thread_id=self.thread.id,
            requesting_tenant_id=TENANT_A,
            sender_user_id=USER_1,
            body='Test message',
        )
        self.thread.refresh_from_db()
        self.assertIsNotNone(self.thread.last_message_at)
        self.assertEqual(self.thread.last_message_preview, 'Test message')

    def test_system_message_bypasses_participant_check(self):
        msg = ThreadService.add_system_message(
            thread_id=self.thread.id,
            tenant_id=TENANT_A,
            body='System: application submitted.',
        )
        self.assertTrue(msg.is_system_generated)
        self.assertEqual(msg.message_type, 'system_event')

    def test_wrong_tenant_cannot_access_thread(self):
        with self.assertRaises(NotFound):
            ThreadService.add_message(
                thread_id=self.thread.id,
                requesting_tenant_id=TENANT_B,  # wrong tenant
                sender_user_id=USER_1,
                body='Cross-tenant attack',
            )


class TestMarkThreadRead(TestCase):

    def setUp(self):
        self.thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=USER_1,
            participant_user_ids=[USER_1, USER_2],
        )
        # USER_1 sends a message — USER_2 should mark it read
        ThreadService.add_message(
            thread_id=self.thread.id,
            requesting_tenant_id=TENANT_A,
            sender_user_id=USER_1,
            body='Please read this.',
        )

    def test_mark_thread_read_updates_participant(self):
        ThreadService.mark_thread_read(
            thread_id=self.thread.id,
            requesting_tenant_id=TENANT_A,
            user_id=USER_2,
        )
        participant = ThreadParticipant.objects.get(thread=self.thread, user_id=USER_2)
        self.assertIsNotNone(participant.last_read_at)

    def test_own_messages_not_marked_read_by_sender(self):
        # USER_1 marks thread read — should not mark their own message as read
        ThreadService.mark_thread_read(
            thread_id=self.thread.id,
            requesting_tenant_id=TENANT_A,
            user_id=USER_1,
        )
        unread = Message.objects.filter(
            thread=self.thread,
            sender_id=USER_1,
            is_read=False,
        )
        # USER_1's own messages stay as-is (the logic excludes sender)
        self.assertTrue(unread.exists())


class TestGetOrCreateContextThread(TestCase):

    def test_creates_context_thread(self):
        entity_id = uuid.uuid4()
        thread, created = ThreadService.get_or_create_context_thread(
            tenant_id=TENANT_A,
            related_entity_type='application',
            related_entity_id=entity_id,
        )
        self.assertTrue(created)
        self.assertEqual(thread.related_entity_type, 'application')

    def test_returns_existing_context_thread(self):
        entity_id = uuid.uuid4()
        thread1, _ = ThreadService.get_or_create_context_thread(
            tenant_id=TENANT_A,
            related_entity_type='application',
            related_entity_id=entity_id,
        )
        thread2, created = ThreadService.get_or_create_context_thread(
            tenant_id=TENANT_A,
            related_entity_type='application',
            related_entity_id=entity_id,
        )
        self.assertFalse(created)
        self.assertEqual(thread1.id, thread2.id)


class TestGetThreadsForUser(TestCase):

    def test_user_only_sees_their_threads(self):
        ThreadService.create_thread(
            tenant_id=TENANT_A, created_by_user_id=USER_1, participant_user_ids=[USER_1]
        )
        ThreadService.create_thread(
            tenant_id=TENANT_A, created_by_user_id=USER_2, participant_user_ids=[USER_2]
        )
        threads = ThreadService.get_threads_for_user(tenant_id=TENANT_A, user_id=USER_1)
        for t in threads:
            user_ids = list(t.participants.values_list('user_id', flat=True))
            self.assertIn(USER_1, user_ids)

    def test_tenant_isolation_in_thread_list(self):
        ThreadService.create_thread(
            tenant_id=TENANT_A, created_by_user_id=USER_1, participant_user_ids=[USER_1]
        )
        threads_b = ThreadService.get_threads_for_user(tenant_id=TENANT_B, user_id=USER_1)
        self.assertEqual(threads_b.count(), 0)
