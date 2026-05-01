"""
QA Tests: In-App Messaging Engine
===================================
Covers all requirements from COMMS-INAPP-MESSAGING-ENGINE-01:

1.  Thread creation (internal, external, entity-linked)
2.  Message sending
3.  External thread (cross-tenant participant)
4.  System / automation messages
5.  Unread tracking (count + mark-read)
6.  Tenant isolation
7.  Permission rules enforcement
8.  Automation message integration
9.  API response stability
10. Participant management (add / remove)
11. Notification triggered on new message
12. Real-time event published on new message

Uses APIRequestFactory + force_authenticate to bypass django-tenants middleware
(consistent with existing test patterns in this codebase).
"""
import uuid
from unittest.mock import patch, MagicMock

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.communications.models import (
    Message,
    MessageThread,
    ThreadParticipant,
    ThreadType,
)
from apps.communications.communication_service import ThreadService
from apps.communications.messaging_service import MessagingService, SYSTEM_SENDER_ID
from apps.communications.messaging_views import (
    MessagingUnreadCountView,
    EntityThreadView,
    ThreadParticipantAddView,
    ThreadParticipantRemoveView,
)

# ── Fixed tenant UUIDs ────────────────────────────────────────────────────────

TENANT_A = uuid.UUID('aaaaaaaa-0000-0000-0000-000000000001')
TENANT_B = uuid.UUID('bbbbbbbb-0000-0000-0000-000000000002')


def _user(email, tenant_id=TENANT_A, role='recruiter'):
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return CustomUser.objects.create_user(
            email=email,
            password='testpass123',
            role=role,
            tenant_id=tenant_id,
        )


# ---------------------------------------------------------------------------
# 1. Thread creation
# ---------------------------------------------------------------------------

class TestThreadCreation(TestCase):
    """Requirement 1: Create thread (internal, external, entity-linked)"""

    def test_create_internal_thread(self):
        u1 = _user('me_create_int1@test.com')
        u2 = _user('me_create_int2@test.com')
        thread = MessagingService.create_internal_thread(
            tenant_id=TENANT_A,
            created_by_user_id=u1.id,
            subject='Discuss candidate Jane',
            participant_user_ids=[u1.id, u2.id],
        )
        self.assertEqual(thread.thread_type, ThreadType.INTERNAL)
        self.assertTrue(thread.is_internal)
        self.assertEqual(ThreadParticipant.objects.filter(thread=thread).count(), 2)

    def test_create_external_company_agency_thread(self):
        u1 = _user('me_ext_co@test.com')
        thread = MessagingService.create_external_thread(
            tenant_id=TENANT_A,
            created_by_user_id=u1.id,
            thread_type=ThreadType.COMPANY_AGENCY,
            subject='Agency submission review',
            participant_user_ids=[u1.id],
        )
        self.assertEqual(thread.thread_type, ThreadType.COMPANY_AGENCY)
        self.assertFalse(thread.is_internal)

    def test_create_recruiter_candidate_thread(self):
        u1 = _user('me_ext_rc@test.com')
        thread = MessagingService.create_external_thread(
            tenant_id=TENANT_A,
            created_by_user_id=u1.id,
            thread_type=ThreadType.RECRUITER_CANDIDATE,
            subject='Interview coordination',
            participant_user_ids=[u1.id],
        )
        self.assertEqual(thread.thread_type, ThreadType.RECRUITER_CANDIDATE)

    def test_invalid_external_type_raises(self):
        u1 = _user('me_ext_invalid@test.com')
        with self.assertRaises(ValueError):
            MessagingService.create_external_thread(
                tenant_id=TENANT_A,
                created_by_user_id=u1.id,
                thread_type='internal',  # internal is not a valid external type
                participant_user_ids=[u1.id],
            )

    def test_entity_linked_thread_created(self):
        u1 = _user('me_entity1@test.com')
        entity_id = uuid.uuid4()
        thread, created = MessagingService.get_or_create_entity_thread(
            tenant_id=TENANT_A,
            entity_type='candidate',
            entity_id=entity_id,
            thread_type='recruiter_candidate',
            subject='Candidate: John Doe',
            created_by_user_id=u1.id,
            participant_user_ids=[u1.id],
        )
        self.assertTrue(created)
        self.assertEqual(thread.related_entity_type, 'candidate')
        self.assertEqual(thread.related_entity_id, entity_id)

    def test_entity_linked_thread_not_duplicated(self):
        u1 = _user('me_entity2@test.com')
        entity_id = uuid.uuid4()
        thread1, _ = MessagingService.get_or_create_entity_thread(
            tenant_id=TENANT_A,
            entity_type='job',
            entity_id=entity_id,
            thread_type='general',
            created_by_user_id=u1.id,
        )
        thread2, created = MessagingService.get_or_create_entity_thread(
            tenant_id=TENANT_A,
            entity_type='job',
            entity_id=entity_id,
            thread_type='general',
            created_by_user_id=u1.id,
        )
        self.assertFalse(created)
        self.assertEqual(thread1.id, thread2.id)


# ---------------------------------------------------------------------------
# 2. Message sending
# ---------------------------------------------------------------------------

class TestMessageSending(TestCase):
    """Requirement 2: Send message, body accessible, thread preview updated"""

    def setUp(self):
        self.u1 = _user('me_msg1@test.com')
        self.u2 = _user('me_msg2@test.com')
        self.thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=self.u1.id,
            participant_user_ids=[self.u1.id, self.u2.id],
        )

    def test_send_message_persists(self):
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            msg = MessagingService.send_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                sender_user_id=self.u1.id,
                body='Hello, let us discuss',
            )
        self.assertIsNotNone(msg.id)
        self.assertEqual(msg.body, 'Hello, let us discuss')
        self.assertFalse(msg.is_system_generated)

    def test_send_message_updates_thread_preview(self):
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            MessagingService.send_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                sender_user_id=self.u1.id,
                body='Preview test message',
            )
        self.thread.refresh_from_db()
        self.assertIn('Preview test message', self.thread.last_message_preview)

    def test_non_participant_cannot_send(self):
        stranger = _user('me_stranger@test.com')
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises((PermissionDenied, Exception)):
            MessagingService.send_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                sender_user_id=stranger.id,
                body='Unauthorized message',
            )

    def test_notification_queued_on_send(self):
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications') as mock_q:
            MessagingService.send_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                sender_user_id=self.u1.id,
                body='Notify test',
                notify_participants=True,
            )
            mock_q.assert_called_once()


# ---------------------------------------------------------------------------
# 3. External thread (cross-tenant participant)
# ---------------------------------------------------------------------------

class TestExternalThread(TestCase):
    """Requirement 3: External thread allows cross-tenant participants"""

    def test_cross_tenant_participant_stored(self):
        u1 = _user('me_cross_co@test.com', TENANT_A)
        external_user_id = uuid.uuid4()
        thread = MessagingService.create_external_thread(
            tenant_id=TENANT_A,
            created_by_user_id=u1.id,
            thread_type=ThreadType.COMPANY_AGENCY,
            subject='Agency review',
            participant_user_ids=[u1.id, external_user_id],
            participant_tenant_ids={str(external_user_id): TENANT_B},
        )
        external_participant = ThreadParticipant.objects.get(
            thread=thread,
            user_id=external_user_id,
        )
        self.assertEqual(external_participant.external_tenant_id, TENANT_B)

    def test_external_thread_is_not_internal(self):
        u1 = _user('me_cross_notinternal@test.com', TENANT_A)
        thread = MessagingService.create_external_thread(
            tenant_id=TENANT_A,
            created_by_user_id=u1.id,
            thread_type=ThreadType.AGENCY_CANDIDATE,
            participant_user_ids=[u1.id],
        )
        self.assertFalse(thread.is_internal)

    def test_tenant_b_cannot_read_tenant_a_internal_thread(self):
        """Agency must not see internal company discussion thread."""
        u_company = _user('me_co_internal@test.com', TENANT_A)
        u_agency = _user('me_ag_spy@test.com', TENANT_B)
        thread = MessagingService.create_internal_thread(
            tenant_id=TENANT_A,
            created_by_user_id=u_company.id,
            participant_user_ids=[u_company.id],
        )
        # ThreadService enforces tenant on get_thread
        from rest_framework.exceptions import NotFound
        with self.assertRaises(NotFound):
            ThreadService.get_thread(
                thread_id=thread.id,
                requesting_tenant_id=TENANT_B,
                requesting_user_id=u_agency.id,
            )


# ---------------------------------------------------------------------------
# 4. System / automation messages
# ---------------------------------------------------------------------------

class TestSystemMessages(TestCase):
    """Requirement 4: System messages posted without participant check"""

    def setUp(self):
        self.u1 = _user('me_sys1@test.com')
        self.thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=self.u1.id,
            participant_user_ids=[self.u1.id],
        )

    def test_system_message_created(self):
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            msg = MessagingService.send_system_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                body='Interview scheduled for tomorrow at 3 PM',
            )
        self.assertTrue(msg.is_system_generated)
        self.assertEqual(msg.message_type, 'system_event')
        self.assertEqual(msg.sender_id, SYSTEM_SENDER_ID)

    def test_system_message_body_stored(self):
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            msg = MessagingService.send_system_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                body='Candidate shortlisted: moved to Technical Interview',
                metadata={'event': 'application.stage_changed'},
            )
        self.assertIn('shortlisted', msg.body)
        self.assertEqual(msg.metadata.get('event'), 'application.stage_changed')

    def test_system_message_has_no_participant_restriction(self):
        """System message must succeed even when no human sender is a participant."""
        orphan_thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=self.u1.id,
            participant_user_ids=[],  # no participants
        )
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            msg = MessagingService.send_system_message(
                thread_id=orphan_thread.id,
                tenant_id=TENANT_A,
                body='Automation event fired',
            )
        self.assertIsNotNone(msg.id)

    def test_system_message_notification_queued(self):
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications') as mock_q:
            MessagingService.send_system_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                body='Offer approved',
                notify_participants=True,
            )
            mock_q.assert_called_once()
            call_kwargs = mock_q.call_args.kwargs
            self.assertTrue(call_kwargs.get('is_system'))


# ---------------------------------------------------------------------------
# 5. Unread tracking
# ---------------------------------------------------------------------------

class TestUnreadTracking(TestCase):
    """Requirement 5: Unread count, mark-thread-read, participant last_read_at"""

    def setUp(self):
        self.sender = _user('me_unread_sender@test.com')
        self.reader = _user('me_unread_reader@test.com')
        self.thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=self.sender.id,
            participant_user_ids=[self.sender.id, self.reader.id],
        )

    def test_unread_count_increments_on_new_message(self):
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            MessagingService.send_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                sender_user_id=self.sender.id,
                body='You have not read this yet',
            )
        count = MessagingService.get_unread_count(
            user_id=self.reader.id,
            tenant_id=TENANT_A,
        )
        self.assertGreaterEqual(count, 1)

    def test_sender_does_not_count_own_messages_as_unread(self):
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            MessagingService.send_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                sender_user_id=self.sender.id,
                body='My own message',
            )
        count = MessagingService.get_unread_count(
            user_id=self.sender.id,
            tenant_id=TENANT_A,
        )
        self.assertEqual(count, 0)

    def test_mark_thread_read_clears_unread(self):
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            MessagingService.send_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                sender_user_id=self.sender.id,
                body='Please read me',
            )
        # Mark read
        ThreadService.mark_thread_read(
            thread_id=self.thread.id,
            requesting_tenant_id=TENANT_A,
            user_id=self.reader.id,
        )
        count = MessagingService.get_unread_count(
            user_id=self.reader.id,
            tenant_id=TENANT_A,
        )
        self.assertEqual(count, 0)

    def test_participant_last_read_at_updated_on_mark_read(self):
        ThreadService.mark_thread_read(
            thread_id=self.thread.id,
            requesting_tenant_id=TENANT_A,
            user_id=self.reader.id,
        )
        participant = ThreadParticipant.objects.get(
            thread=self.thread,
            user_id=self.reader.id,
        )
        self.assertIsNotNone(participant.last_read_at)

    def test_thread_unread_count_for_specific_thread(self):
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            for i in range(3):
                MessagingService.send_message(
                    thread_id=self.thread.id,
                    tenant_id=TENANT_A,
                    sender_user_id=self.sender.id,
                    body=f'Message {i}',
                )
        count = MessagingService.get_thread_unread_count(
            thread_id=self.thread.id,
            user_id=self.reader.id,
            tenant_id=TENANT_A,
        )
        self.assertEqual(count, 3)

    def test_unread_count_api_returns_correct_value(self):
        factory = APIRequestFactory()
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            MessagingService.send_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                sender_user_id=self.sender.id,
                body='API unread test',
            )
        request = factory.get('/messages/unread-count/')
        force_authenticate(request, user=self.reader)
        response = MessagingUnreadCountView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('unread_message_count', response.data['data'])
        self.assertGreaterEqual(response.data['data']['unread_message_count'], 1)


# ---------------------------------------------------------------------------
# 6. Tenant isolation
# ---------------------------------------------------------------------------

class TestTenantIsolation(TestCase):
    """Requirement 6: Cross-tenant access must be blocked at all layers"""

    def test_thread_list_only_returns_own_tenant_threads(self):
        u_a = _user('me_iso_a@test.com', TENANT_A)
        u_b = _user('me_iso_b@test.com', TENANT_B)

        thread_a = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=u_a.id,
            participant_user_ids=[u_a.id],
        )
        thread_b = ThreadService.create_thread(
            tenant_id=TENANT_B,
            created_by_user_id=u_b.id,
            participant_user_ids=[u_b.id],
        )

        threads_a = ThreadService.get_threads_for_user(
            tenant_id=TENANT_A,
            user_id=u_a.id,
        )
        thread_ids_a = [str(t.id) for t in threads_a]
        self.assertIn(str(thread_a.id), thread_ids_a)
        self.assertNotIn(str(thread_b.id), thread_ids_a)

    def test_unread_count_isolated_by_tenant(self):
        u_a = _user('me_iso_unread_a@test.com', TENANT_A)
        u_b = _user('me_iso_unread_b@test.com', TENANT_B)

        thread_b = ThreadService.create_thread(
            tenant_id=TENANT_B,
            created_by_user_id=u_b.id,
            participant_user_ids=[u_b.id],
        )
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            MessagingService.send_message(
                thread_id=thread_b.id,
                tenant_id=TENANT_B,
                sender_user_id=u_b.id,
                body='Tenant B message',
            )

        # Tenant A user should see zero unread (they are not in Tenant B threads)
        count = MessagingService.get_unread_count(
            user_id=u_a.id,
            tenant_id=TENANT_A,
        )
        self.assertEqual(count, 0)

    def test_message_write_to_other_tenant_thread_blocked(self):
        u_a = _user('me_iso_write_a@test.com', TENANT_A)
        u_b = _user('me_iso_write_b@test.com', TENANT_B)

        thread_b = ThreadService.create_thread(
            tenant_id=TENANT_B,
            created_by_user_id=u_b.id,
            participant_user_ids=[u_b.id],
        )

        from rest_framework.exceptions import NotFound
        with self.assertRaises((NotFound, Exception)):
            MessagingService.send_message(
                thread_id=thread_b.id,
                tenant_id=TENANT_A,  # wrong tenant
                sender_user_id=u_a.id,
                body='Cross-tenant injection attempt',
            )


# ---------------------------------------------------------------------------
# 7. Permission rules
# ---------------------------------------------------------------------------

class TestPermissions(TestCase):
    """Requirement 7: Only participants can read/write; owners can manage participants"""

    def setUp(self):
        self.owner = _user('me_perm_owner@test.com')
        self.member = _user('me_perm_member@test.com')
        self.stranger = _user('me_perm_stranger@test.com')
        self.thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=self.owner.id,
            participant_user_ids=[self.owner.id, self.member.id],
        )

    def test_non_participant_cannot_read_messages(self):
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises((PermissionDenied, Exception)):
            ThreadService.get_messages(
                thread_id=self.thread.id,
                requesting_tenant_id=TENANT_A,
                requesting_user_id=self.stranger.id,
            )

    def test_non_participant_cannot_send_message(self):
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises((PermissionDenied, Exception)):
            MessagingService.send_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                sender_user_id=self.stranger.id,
                body='Intruder message',
            )

    def test_only_participant_can_add_new_participant(self):
        """Strangers cannot add participants."""
        from rest_framework.exceptions import PermissionDenied
        new_user = _user('me_perm_new@test.com')
        with self.assertRaises((PermissionDenied, Exception)):
            MessagingService.add_participant(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                requesting_user_id=self.stranger.id,
                new_user_id=new_user.id,
            )

    def test_participant_can_add_new_participant(self):
        new_user = _user('me_perm_add@test.com')
        participant = MessagingService.add_participant(
            thread_id=self.thread.id,
            tenant_id=TENANT_A,
            requesting_user_id=self.member.id,
            new_user_id=new_user.id,
        )
        self.assertEqual(participant.user_id, new_user.id)

    def test_member_cannot_remove_other_member(self):
        from rest_framework.exceptions import PermissionDenied
        member_participant = ThreadParticipant.objects.get(
            thread=self.thread,
            user_id=self.member.id,
        )
        with self.assertRaises((PermissionDenied, Exception)):
            MessagingService.remove_participant(
                participant_id=member_participant.id,
                tenant_id=TENANT_A,
                requesting_user_id=self.stranger.id,
            )

    def test_user_can_remove_themselves(self):
        member_participant = ThreadParticipant.objects.get(
            thread=self.thread,
            user_id=self.member.id,
        )
        result = MessagingService.remove_participant(
            participant_id=member_participant.id,
            tenant_id=TENANT_A,
            requesting_user_id=self.member.id,  # removing self
        )
        self.assertTrue(result)
        member_participant.refresh_from_db()
        self.assertFalse(member_participant.is_active)


# ---------------------------------------------------------------------------
# 8. Automation integration
# ---------------------------------------------------------------------------

class TestAutomationIntegration(TestCase):
    """Requirement 8: Automation engine can post system messages async"""

    def setUp(self):
        self.u1 = _user('me_auto1@test.com')
        self.thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=self.u1.id,
            participant_user_ids=[self.u1.id],
        )

    def test_send_system_message_via_service(self):
        """Direct service call (used by automation synchronously)."""
        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            msg = MessagingService.send_system_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                body='Offer approved — awaiting candidate acceptance',
                metadata={'event': 'offer.approved', 'offer_id': str(uuid.uuid4())},
            )
        self.assertTrue(msg.is_system_generated)
        self.assertIn('approved', msg.body)

    def test_automation_celery_task_calls_service(self):
        """send_automation_system_message_task delegates to MessagingService."""
        from apps.communications.messaging_tasks import send_automation_system_message_task

        with patch(
            'apps.communications.messaging_service.MessagingService._queue_participant_notifications'
        ):
            send_automation_system_message_task(
                thread_id=str(self.thread.id),
                tenant_id=str(TENANT_A),
                body='Candidate shortlisted',
                metadata={'event': 'candidate.shortlisted'},
            )

        msg = Message.objects.filter(
            thread=self.thread,
            is_system_generated=True,
        ).last()
        self.assertIsNotNone(msg)
        self.assertIn('shortlisted', msg.body)

    def test_notify_task_creates_notification_for_participants(self):
        """notify_message_participants_task creates in-app notifications."""
        from apps.communications.messaging_tasks import notify_message_participants_task

        u2 = _user('me_auto_recv@test.com')
        ThreadService.add_participant(
            thread_id=self.thread.id,
            requesting_tenant_id=TENANT_A,
            user_id=u2.id,
        )

        with patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            msg = MessagingService.send_message(
                thread_id=self.thread.id,
                tenant_id=TENANT_A,
                sender_user_id=self.u1.id,
                body='Automation notify test',
                notify_participants=False,
            )

        with patch('apps.communications.messaging_tasks.message_fallback_email_task') as mock_fb:
            notify_message_participants_task(
                thread_id=str(self.thread.id),
                message_id=str(msg.id),
                sender_user_id=str(self.u1.id),
                tenant_id=str(TENANT_A),
            )
            # Fallback scheduled for u2 (not sender)
            mock_fb.apply_async.assert_called()

        from apps.communications.models import Notification
        notif = Notification.objects.filter(
            user_id=u2.id,
            tenant_id=TENANT_A,
        ).last()
        self.assertIsNotNone(notif)
        self.assertIn('message', notif.notification_type.lower())


# ---------------------------------------------------------------------------
# 9. API response stability
# ---------------------------------------------------------------------------

class TestAPIResponseStability(TestCase):
    """Requirement 9: API endpoints return correct shapes; no crashes on edge cases"""

    factory = APIRequestFactory()

    def setUp(self):
        self.user = _user('me_api_stable@test.com')

    def test_unread_count_returns_zero_for_fresh_user(self):
        request = self.factory.get('/messages/unread-count/')
        force_authenticate(request, user=self.user)
        response = MessagingUnreadCountView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['unread_message_count'], 0)

    def test_entity_thread_returns_empty_list_when_no_threads(self):
        request = self.factory.get(
            '/messages/threads/entity/',
            {'entity_type': 'candidate', 'entity_id': str(uuid.uuid4())},
        )
        force_authenticate(request, user=self.user)
        response = EntityThreadView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['threads'], [])

    def test_entity_thread_missing_params_returns_400(self):
        request = self.factory.get('/messages/threads/entity/')
        force_authenticate(request, user=self.user)
        response = EntityThreadView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_participant_missing_user_id_returns_400(self):
        thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=self.user.id,
            participant_user_ids=[self.user.id],
        )
        request = self.factory.post(
            f'/messages/threads/{thread.id}/participants/',
            {},
            format='json',
        )
        force_authenticate(request, user=self.user)
        response = ThreadParticipantAddView.as_view()(request, pk=thread.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_unread_count_rejected(self):
        request = self.factory.get('/messages/unread-count/')
        response = MessagingUnreadCountView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_entity_thread_create_or_get_via_post(self):
        entity_id = uuid.uuid4()
        request = self.factory.post(
            '/messages/threads/entity/',
            {
                'entity_type': 'interview',
                'entity_id': str(entity_id),
                'thread_type': 'interview_coordination',
                'subject': 'Interview coordination thread',
            },
            format='json',
        )
        force_authenticate(request, user=self.user)
        response = EntityThreadView.as_view()(request)
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
        ])
        self.assertIn('thread', response.data['data'])
        self.assertIn('created', response.data['data'])


# ---------------------------------------------------------------------------
# 10. Real-time event publishing
# ---------------------------------------------------------------------------

class TestRealtimePublishing(TestCase):
    """Requirement 12: Real-time event published after message send"""

    def test_realtime_event_published_on_message_send(self):
        u1 = _user('me_rt1@test.com')
        u2 = _user('me_rt2@test.com')
        thread = ThreadService.create_thread(
            tenant_id=TENANT_A,
            created_by_user_id=u1.id,
            participant_user_ids=[u1.id, u2.id],
        )
        with patch('apps.communications.realtime.RealtimePublisher.publish_message') as mock_pub, \
             patch('apps.communications.messaging_service.MessagingService._queue_participant_notifications'):
            MessagingService.send_message(
                thread_id=thread.id,
                tenant_id=TENANT_A,
                sender_user_id=u1.id,
                body='Real-time test',
            )
            mock_pub.assert_called_once()
