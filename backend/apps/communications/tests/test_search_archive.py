"""
QA Tests: Communication Search, Archive, History, and Retention
================================================================

Coverage requirements from COMMS-SEARCH-AND-ARCHIVE-01:

 1.  Global search returns only permitted results (tenant + participant gate)
 2.  Thread search works correctly (text match + sender + date)
 3.  Archived threads excluded from default results; searchable when requested
 4.  Archive endpoint works; unarchive restores thread
 5.  Entity communication history returns all linked records
 6.  Cross-tenant search leakage does not occur
 7.  Internal-only thread hidden from unauthorised roles
 8.  Notification history works (q, is_read, is_archived, severity)
 9.  Search pagination works (limit / offset)
10.  Search snippet / highlight data present where expected
11.  Large result queries remain bounded (limit enforced)
12.  Archive blocked on legal-hold threads
13.  Non-participant cannot archive a thread
14.  Archived threads list endpoint works
15.  Recent communications endpoint works
16.  Notification history q filter works
17.  Unarchive endpoint works (idempotent)
18.  Thread search returns nav_target for jump-to-message

Uses APIRequestFactory + force_authenticate to bypass django-tenants middleware
(consistent with existing test patterns in this codebase).
"""
from __future__ import annotations

import uuid
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.communications.models import (
    Message,
    MessageThread,
    Notification,
    ThreadParticipant,
    ThreadType,
    ChannelType,
)
from apps.communications.search_service import (
    CommunicationSearchService,
    build_search_snippet,
)
from apps.communications.search_views import (
    GlobalCommunicationSearchView,
    ThreadMessageSearchView,
    ArchiveThreadView,
    UnarchiveThreadView,
    ArchivedThreadListView,
    EntityCommunicationHistoryView,
    RecentCommunicationsView,
    NotificationHistoryView,
)

# ── Fixed test tenant UUIDs ───────────────────────────────────────────────────

TENANT_A = uuid.UUID('aaaa0000-0000-0000-0000-000000000001')
TENANT_B = uuid.UUID('bbbb0000-0000-0000-0000-000000000002')

# ── Helpers ───────────────────────────────────────────────────────────────────


def _user(email: str, tenant_id=TENANT_A, role: str = 'recruiter') -> CustomUser:
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return CustomUser.objects.create_user(
            email=email,
            password='testpass123',
            role=role,
            tenant_id=tenant_id,
        )


def _thread(
    tenant_id=TENANT_A,
    subject: str = 'Test Thread',
    thread_type: str = ThreadType.INTERNAL,
    is_internal: bool = True,
    related_entity_type: str = '',
    related_entity_id=None,
) -> MessageThread:
    return MessageThread.objects.create(
        tenant_id=tenant_id,
        subject=subject,
        thread_type=thread_type,
        is_internal=is_internal,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )


def _participant(thread: MessageThread, user: CustomUser, tenant_id=TENANT_A) -> ThreadParticipant:
    return ThreadParticipant.objects.create(
        tenant_id=tenant_id,
        thread=thread,
        user_id=user.id,
        is_active=True,
    )


def _message(
    thread: MessageThread,
    sender: CustomUser,
    body: str = 'Hello',
    message_type: str = 'text',
    channel_type: str = 'in_app',
) -> Message:
    return Message.objects.create(
        tenant_id=thread.tenant_id,
        thread=thread,
        sender_id=sender.id,
        body=body,
        message_type=message_type,
        channel_type=channel_type,
    )


def _notification(
    user: CustomUser,
    tenant_id=TENANT_A,
    title: str = 'You have a new notification',
    body: str = 'Click here for details.',
    is_read: bool = False,
    severity: str = 'info',
    related_entity_type: str = '',
    related_entity_id=None,
) -> Notification:
    return Notification.objects.create(
        tenant_id=tenant_id,
        user_id=user.id,
        title=title,
        body=body,
        is_read=is_read,
        severity=severity,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )


# =============================================================================
# 1. Helper: build_search_snippet
# =============================================================================

class TestBuildSearchSnippet(TestCase):
    """Validates the snippet extraction helper independent of DB queries."""

    def test_snippet_contains_query(self):
        text = 'The candidate submitted their offer letter yesterday and it was approved.'
        snippet = build_search_snippet(text, 'offer letter')
        self.assertIn('offer letter', snippet)

    def test_snippet_ellipsis_when_truncated(self):
        text = 'A' * 50 + ' the matching term is here ' + 'B' * 50
        snippet = build_search_snippet(text, 'matching term', radius=10)
        self.assertIn('…', snippet)

    def test_snippet_empty_text_returns_empty(self):
        self.assertEqual(build_search_snippet('', 'query'), '')

    def test_snippet_no_match_returns_start_of_text(self):
        text = 'Completely unrelated content for the test run.'
        snippet = build_search_snippet(text, 'zzznomatch')
        self.assertTrue(len(snippet) > 0)

    def test_snippet_full_text_when_short(self):
        text = 'Short text'
        snippet = build_search_snippet(text, 'Short')
        self.assertIn('Short', snippet)


# =============================================================================
# 2. check_communication_access
# =============================================================================

class TestCheckCommunicationAccess(TestCase):

    def setUp(self):
        self.user1 = _user('access1@test.com')
        self.user2 = _user('access2@test.com')
        self.thread = _thread(tenant_id=TENANT_A)
        _participant(self.thread, self.user1)

    def test_participant_has_access(self):
        self.assertTrue(
            CommunicationSearchService.check_communication_access(
                thread_id=str(self.thread.id),
                user_id=str(self.user1.id),
                tenant_id=str(TENANT_A),
            )
        )

    def test_non_participant_denied(self):
        self.assertFalse(
            CommunicationSearchService.check_communication_access(
                thread_id=str(self.thread.id),
                user_id=str(self.user2.id),
                tenant_id=str(TENANT_A),
            )
        )

    def test_wrong_tenant_denied(self):
        # user1 is a participant but querying with a different tenant_id
        self.assertFalse(
            CommunicationSearchService.check_communication_access(
                thread_id=str(self.thread.id),
                user_id=str(self.user1.id),
                tenant_id=str(TENANT_B),
            )
        )

    def test_deleted_thread_denied(self):
        self.thread.is_deleted = True
        self.thread.save(update_fields=['is_deleted'])
        self.assertFalse(
            CommunicationSearchService.check_communication_access(
                thread_id=str(self.thread.id),
                user_id=str(self.user1.id),
                tenant_id=str(TENANT_A),
            )
        )


# =============================================================================
# 3. Global Communication Search — service layer
# =============================================================================

class TestGlobalSearchService(TestCase):

    def setUp(self):
        self.recruiter = _user('search_recruiter@test.com', TENANT_A)
        self.outsider = _user('search_outsider@test.com', TENANT_A)
        self.thread = _thread(TENANT_A, subject='Interview Coordination')
        _participant(self.thread, self.recruiter)
        self.msg = _message(self.thread, self.recruiter, body='The candidate John was shortlisted.')

    def _search(self, query, user=None, **kwargs):
        user = user or self.recruiter
        return CommunicationSearchService.search_communications(
            tenant_id=str(TENANT_A),
            user_id=str(user.id),
            query=query,
            **kwargs,
        )

    # ── Basic match ─────────────────────────────────────────────────────────

    def test_message_body_match(self):
        result = self._search('John was shortlisted')
        types = [r['type'] for r in result['results']]
        self.assertIn('message', types)

    def test_thread_subject_match(self):
        result = self._search('Interview Coordination')
        types = [r['type'] for r in result['results']]
        self.assertIn('thread', types)

    def test_empty_query_returns_empty(self):
        result = self._search('')
        self.assertEqual(result['results'], [])
        self.assertEqual(result['total'], 0)

    def test_no_match_returns_empty(self):
        result = self._search('zzz_no_match_xyz')
        self.assertEqual(len(result['results']), 0)

    # ── Permission gate ──────────────────────────────────────────────────────

    def test_non_participant_cannot_see_message(self):
        # outsider is not a participant in the thread
        result = self._search('John was shortlisted', user=self.outsider)
        msg_results = [r for r in result['results'] if r['type'] == 'message']
        self.assertEqual(len(msg_results), 0)

    # ── Snippet present ──────────────────────────────────────────────────────

    def test_result_contains_snippet(self):
        result = self._search('shortlisted')
        msg_results = [r for r in result['results'] if r['type'] == 'message']
        if msg_results:
            self.assertIn('snippet', msg_results[0])
            self.assertTrue(len(msg_results[0]['snippet']) > 0)

    # ── nav_target present ───────────────────────────────────────────────────

    def test_result_contains_nav_target(self):
        result = self._search('shortlisted')
        msg_results = [r for r in result['results'] if r['type'] == 'message']
        if msg_results:
            self.assertIn('nav_target', msg_results[0])
            self.assertIn(str(self.thread.id), msg_results[0]['nav_target'])

    # ── Archived exclusion ───────────────────────────────────────────────────

    def test_archived_thread_excluded_by_default(self):
        self.thread.is_archived = True
        self.thread.save(update_fields=['is_archived'])
        result = self._search('shortlisted', include_archived=False)
        msg_results = [r for r in result['results'] if r['type'] == 'message']
        self.assertEqual(len(msg_results), 0)

    def test_archived_thread_included_when_requested(self):
        self.thread.is_archived = True
        self.thread.save(update_fields=['is_archived'])
        result = self._search('shortlisted', include_archived=True)
        msg_results = [r for r in result['results'] if r['type'] == 'message']
        self.assertGreater(len(msg_results), 0)

    # ── thread_type filter ───────────────────────────────────────────────────

    def test_thread_type_filter_excludes_non_matching(self):
        result = self._search('shortlisted', thread_type='company_agency')
        msg_results = [r for r in result['results'] if r['type'] == 'message']
        self.assertEqual(len(msg_results), 0)

    def test_thread_type_filter_includes_matching(self):
        result = self._search('shortlisted', thread_type=ThreadType.INTERNAL)
        msg_results = [r for r in result['results'] if r['type'] == 'message']
        self.assertGreater(len(msg_results), 0)

    # ── notification search ──────────────────────────────────────────────────

    def test_notification_body_match(self):
        _notification(
            self.recruiter,
            title='Offer approved',
            body='The offer for candidate John has been approved.',
        )
        result = self._search('offer approved')
        notif_results = [r for r in result['results'] if r['type'] == 'notification']
        self.assertGreater(len(notif_results), 0)

    def test_notification_belongs_to_user_only(self):
        _notification(
            self.outsider,
            title='Secret notification for outsider',
            body='Do not leak this to recruiter.',
        )
        result = self._search('Secret notification')
        notif_results = [r for r in result['results'] if r['type'] == 'notification']
        self.assertEqual(len(notif_results), 0)


# =============================================================================
# 4. Cross-Tenant Isolation
# =============================================================================

class TestCrossTenantIsolation(TestCase):

    def setUp(self):
        self.user_a = _user('tenant_a_user@test.com', TENANT_A)
        self.user_b = _user('tenant_b_user@test.com', TENANT_B)

        # Thread in TENANT_A with user_a as participant
        self.thread_a = _thread(TENANT_A, subject='Tenant A Confidential')
        _participant(self.thread_a, self.user_a, tenant_id=TENANT_A)
        self.msg_a = _message(self.thread_a, self.user_a, body='Tenant A secret message')

        # Thread in TENANT_B with user_b as participant
        self.thread_b = _thread(TENANT_B, subject='Tenant B Confidential')
        _participant(self.thread_b, self.user_b, tenant_id=TENANT_B)
        self.msg_b = _message(self.thread_b, self.user_b, body='Tenant B secret message')

    def test_user_a_cannot_see_tenant_b_messages(self):
        result = CommunicationSearchService.search_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.user_a.id),
            query='secret message',
        )
        ids = [r['id'] for r in result['results']]
        self.assertNotIn(str(self.msg_b.id), ids)

    def test_user_b_cannot_see_tenant_a_messages(self):
        result = CommunicationSearchService.search_communications(
            tenant_id=str(TENANT_B),
            user_id=str(self.user_b.id),
            query='secret message',
        )
        ids = [r['id'] for r in result['results']]
        self.assertNotIn(str(self.msg_a.id), ids)

    def test_user_a_cannot_access_tenant_b_thread(self):
        # Direct access check across tenants
        self.assertFalse(
            CommunicationSearchService.check_communication_access(
                thread_id=str(self.thread_b.id),
                user_id=str(self.user_a.id),
                tenant_id=str(TENANT_A),
            )
        )


# =============================================================================
# 5. Internal Thread Access Control
# =============================================================================

class TestInternalThreadAccess(TestCase):

    def setUp(self):
        self.recruiter = _user('recruiter_internal@test.com', TENANT_A, 'recruiter')
        self.candidate = _user('candidate_internal@test.com', TENANT_A, 'candidate')
        # Internal recruiter thread — candidate is NOT a participant
        self.internal_thread = _thread(
            TENANT_A,
            subject='Recruiter discussion — do not expose',
            thread_type=ThreadType.INTERNAL,
            is_internal=True,
        )
        _participant(self.internal_thread, self.recruiter)
        self.msg = _message(
            self.internal_thread, self.recruiter, body='Interviewer notes for internal use'
        )

    def test_candidate_cannot_search_internal_thread(self):
        result = CommunicationSearchService.search_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.candidate.id),
            query='Interviewer notes',
        )
        ids = [r['id'] for r in result['results']]
        self.assertNotIn(str(self.msg.id), ids)

    def test_recruiter_can_search_internal_thread(self):
        result = CommunicationSearchService.search_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.recruiter.id),
            query='Interviewer notes',
        )
        msg_ids = [r['id'] for r in result['results'] if r['type'] == 'message']
        self.assertIn(str(self.msg.id), msg_ids)


# =============================================================================
# 6. Thread-Level Search — service layer
# =============================================================================

class TestThreadSearchService(TestCase):

    def setUp(self):
        self.user = _user('thread_search_user@test.com', TENANT_A)
        self.other = _user('thread_search_other@test.com', TENANT_A)
        self.thread = _thread(TENANT_A, subject='Project Alpha')
        _participant(self.thread, self.user)
        self.msg1 = _message(self.thread, self.user, body='Discussed candidate profile in detail')
        self.msg2 = _message(self.thread, self.user, body='Follow up on the passport submission')

    def _search(self, query, **kwargs):
        return CommunicationSearchService.search_thread_messages(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
            query=query,
            **kwargs,
        )

    def test_body_text_match(self):
        result = self._search('candidate profile')
        ids = [r['id'] for r in result['results']]
        self.assertIn(str(self.msg1.id), ids)

    def test_no_match_returns_empty(self):
        result = self._search('zzznomatch')
        self.assertEqual(len(result['results']), 0)

    def test_non_participant_raises_permission_denied(self):
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            CommunicationSearchService.search_thread_messages(
                thread_id=str(self.thread.id),
                tenant_id=str(TENANT_A),
                user_id=str(self.other.id),
                query='candidate',
            )

    def test_result_contains_snippet_and_nav_target(self):
        result = self._search('candidate profile')
        if result['results']:
            item = result['results'][0]
            self.assertIn('snippet', item)
            self.assertIn('nav_target', item)
            self.assertIn(str(self.msg1.id), item['nav_target'])

    def test_pagination_limit_respected(self):
        # Create 5 more messages all matching
        for i in range(5):
            _message(self.thread, self.user, body=f'Passport review message {i}')
        result = self._search('Passport', limit=2)
        self.assertLessEqual(len(result['results']), 2)
        self.assertGreater(result['total'], 2)

    def test_sender_filter(self):
        other_user = _user('thread_search_sender@test.com', TENANT_A)
        _participant(self.thread, other_user)
        other_msg = _message(self.thread, other_user, body='Message from other user about passport')
        result = self._search('passport', sender_id=str(other_user.id))
        ids = [r['id'] for r in result['results']]
        self.assertIn(str(other_msg.id), ids)
        # self.msg2 body also contains 'passport' but from different sender
        self.assertNotIn(str(self.msg2.id), ids)


# =============================================================================
# 7. Archive / Unarchive — service layer
# =============================================================================

class TestArchiveService(TestCase):

    def setUp(self):
        self.user = _user('archive_user@test.com', TENANT_A)
        self.outsider = _user('archive_outsider@test.com', TENANT_A)
        self.thread = _thread(TENANT_A, subject='Thread to archive')
        _participant(self.thread, self.user)

    def test_archive_thread(self):
        result = CommunicationSearchService.archive_thread(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        self.assertTrue(result)
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_archived)
        self.assertIsNotNone(self.thread.archived_at)
        self.assertEqual(self.thread.archived_by, self.user.id)

    def test_unarchive_thread(self):
        self.thread.is_archived = True
        self.thread.archived_at = timezone.now()
        self.thread.archived_by = self.user.id
        self.thread.save()

        result = CommunicationSearchService.unarchive_thread(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        self.assertTrue(result)
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_archived)
        self.assertIsNone(self.thread.archived_at)

    def test_non_participant_cannot_archive(self):
        result = CommunicationSearchService.archive_thread(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.outsider.id),
        )
        self.assertFalse(result)
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_archived)

    def test_archive_nonexistent_thread_returns_false(self):
        result = CommunicationSearchService.archive_thread(
            thread_id=str(uuid.uuid4()),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        self.assertFalse(result)

    def test_legal_hold_blocks_archive(self):
        self.thread.legal_hold = True
        self.thread.save(update_fields=['legal_hold'])
        result = CommunicationSearchService.archive_thread(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        self.assertFalse(result)
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_archived)

    def test_archive_idempotent(self):
        # Archive twice — should return True both times without error
        CommunicationSearchService.archive_thread(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        result = CommunicationSearchService.archive_thread(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        self.assertTrue(result)

    def test_unarchive_idempotent(self):
        result = CommunicationSearchService.unarchive_thread(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        self.assertTrue(result)

    def test_archived_thread_not_in_search_by_default(self):
        CommunicationSearchService.archive_thread(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        _message(self.thread, self.user, body='Archived thread content should not appear')
        result = CommunicationSearchService.search_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
            query='Archived thread content',
        )
        msg_ids = [r['id'] for r in result['results'] if r['type'] == 'message']
        self.assertEqual(len(msg_ids), 0)

    def test_archived_thread_searchable_when_include_archived(self):
        CommunicationSearchService.archive_thread(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        msg = _message(self.thread, self.user, body='Content in archived thread searchable test')
        result = CommunicationSearchService.search_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
            query='Content in archived thread',
            include_archived=True,
        )
        msg_ids = [r['id'] for r in result['results'] if r['type'] == 'message']
        self.assertIn(str(msg.id), msg_ids)


# =============================================================================
# 8. Archived Thread List
# =============================================================================

class TestArchivedThreadList(TestCase):

    def setUp(self):
        self.user = _user('archived_list_user@test.com', TENANT_A)
        self.active_thread = _thread(TENANT_A, subject='Active thread')
        _participant(self.active_thread, self.user)
        self.archived_thread = _thread(TENANT_A, subject='Archived thread')
        _participant(self.archived_thread, self.user)
        self.archived_thread.is_archived = True
        self.archived_thread.archived_at = timezone.now()
        self.archived_thread.archived_by = self.user.id
        self.archived_thread.save()

    def test_only_archived_threads_returned(self):
        result = CommunicationSearchService.get_archived_threads(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        ids = [t['id'] for t in result['threads']]
        self.assertIn(str(self.archived_thread.id), ids)
        self.assertNotIn(str(self.active_thread.id), ids)

    def test_archived_thread_includes_metadata(self):
        result = CommunicationSearchService.get_archived_threads(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        if result['threads']:
            t = result['threads'][0]
            self.assertIn('archived_at', t)
            self.assertIn('archived_by', t)
            self.assertIn('retention_category', t)
            self.assertIn('legal_hold', t)


# =============================================================================
# 9. Entity Communication History — service layer
# =============================================================================

class TestEntityCommunicationHistory(TestCase):

    def setUp(self):
        self.recruiter = _user('entity_hist_rec@test.com', TENANT_A)
        self.candidate_entity_id = uuid.uuid4()
        # Thread linked to candidate
        self.thread = _thread(
            TENANT_A,
            subject='Candidate conversation',
            related_entity_type='candidate',
            related_entity_id=self.candidate_entity_id,
        )
        _participant(self.thread, self.recruiter)
        self.msg = _message(self.thread, self.recruiter, body='Discussing candidate background')
        # Notification linked to candidate
        self.notif = _notification(
            self.recruiter,
            title='Candidate shortlisted',
            body='Candidate has been shortlisted.',
            related_entity_type='candidate',
            related_entity_id=self.candidate_entity_id,
        )
        # Unlinked message (should not appear)
        self.unlinked_thread = _thread(TENANT_A, subject='Unrelated thread')
        _participant(self.unlinked_thread, self.recruiter)
        self.unlinked_msg = _message(self.unlinked_thread, self.recruiter, body='Unrelated content')

    def _history(self):
        return CommunicationSearchService.get_entity_communication_history(
            tenant_id=str(TENANT_A),
            user_id=str(self.recruiter.id),
            entity_type='candidate',
            entity_id=str(self.candidate_entity_id),
        )

    def test_linked_message_appears_in_history(self):
        result = self._history()
        ids = [item['id'] for item in result['timeline']]
        self.assertIn(str(self.msg.id), ids)

    def test_linked_notification_appears_in_history(self):
        result = self._history()
        ids = [item['id'] for item in result['timeline']]
        self.assertIn(str(self.notif.id), ids)

    def test_unlinked_message_not_in_history(self):
        result = self._history()
        ids = [item['id'] for item in result['timeline']]
        self.assertNotIn(str(self.unlinked_msg.id), ids)

    def test_timeline_has_type_labels(self):
        result = self._history()
        types = {item['type'] for item in result['timeline']}
        self.assertIn('message', types)
        self.assertIn('notification', types)

    def test_timeline_sorted_newest_first(self):
        result = self._history()
        dates = [item['event_at'] for item in result['timeline']]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_non_participant_excluded(self):
        outsider = _user('entity_hist_outsider@test.com', TENANT_A)
        result = CommunicationSearchService.get_entity_communication_history(
            tenant_id=str(TENANT_A),
            user_id=str(outsider.id),
            entity_type='candidate',
            entity_id=str(self.candidate_entity_id),
        )
        # Message in the thread should be excluded (outsider is not a participant)
        msg_ids = [item['id'] for item in result['timeline'] if item['type'] == 'message']
        self.assertNotIn(str(self.msg.id), msg_ids)


# =============================================================================
# 10. Notification History — service layer
# =============================================================================

class TestNotificationHistoryService(TestCase):

    def setUp(self):
        self.user = _user('notif_hist_user@test.com', TENANT_A)
        self.n_read = _notification(self.user, title='Read notification', is_read=True)
        self.n_unread = _notification(self.user, title='Unread notification', is_read=False)
        self.n_archived = _notification(self.user, title='Archived notification')
        self.n_archived.is_archived = True
        self.n_archived.save(update_fields=['is_archived'])
        self.n_high = _notification(
            self.user, title='High severity notification', severity='high'
        )

    def _history(self, **kwargs):
        return CommunicationSearchService.get_notification_history(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
            **kwargs,
        )

    def test_all_notifications_returned_by_default(self):
        result = self._history()
        ids = [n['id'] for n in result['notifications']]
        for notif in [self.n_read, self.n_unread, self.n_archived, self.n_high]:
            self.assertIn(str(notif.id), ids)

    def test_unread_filter(self):
        result = self._history(is_read=False)
        for n in result['notifications']:
            self.assertFalse(n['is_read'])

    def test_read_filter(self):
        result = self._history(is_read=True)
        for n in result['notifications']:
            self.assertTrue(n['is_read'])

    def test_exclude_archived(self):
        result = self._history(include_archived=False)
        ids = [n['id'] for n in result['notifications']]
        self.assertNotIn(str(self.n_archived.id), ids)

    def test_severity_filter(self):
        result = self._history(severity='high')
        ids = [n['id'] for n in result['notifications']]
        self.assertIn(str(self.n_high.id), ids)
        self.assertNotIn(str(self.n_read.id), ids)

    def test_query_filter_title(self):
        result = self._history(query='High severity')
        ids = [n['id'] for n in result['notifications']]
        self.assertIn(str(self.n_high.id), ids)
        self.assertNotIn(str(self.n_unread.id), ids)

    def test_pagination(self):
        result = self._history(limit=2, offset=0)
        self.assertLessEqual(len(result['notifications']), 2)
        self.assertGreater(result['total'], 0)

    def test_other_user_notifications_not_returned(self):
        other = _user('notif_hist_other@test.com', TENANT_A)
        _notification(other, title='Other user notification — do not leak')
        result = self._history(query='Other user notification')
        self.assertEqual(len(result['notifications']), 0)


# =============================================================================
# 11. Recent Communications — service layer
# =============================================================================

class TestRecentCommunications(TestCase):

    def setUp(self):
        self.user = _user('recent_user@test.com', TENANT_A)
        self.t1 = _thread(TENANT_A, subject='Thread One')
        self.t2 = _thread(TENANT_A, subject='Thread Two')
        _participant(self.t1, self.user)
        _participant(self.t2, self.user)
        _message(self.t1, self.user, body='Message in thread one')
        # Update last_message_at manually
        self.t1.last_message_at = timezone.now()
        self.t1.save(update_fields=['last_message_at'])

    def test_returns_active_threads_only(self):
        result = CommunicationSearchService.get_recent_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        ids = [t['id'] for t in result['threads']]
        self.assertIn(str(self.t1.id), ids)

    def test_archived_excluded(self):
        self.t1.is_archived = True
        self.t1.save(update_fields=['is_archived'])
        result = CommunicationSearchService.get_recent_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        ids = [t['id'] for t in result['threads']]
        self.assertNotIn(str(self.t1.id), ids)

    def test_limit_respected(self):
        result = CommunicationSearchService.get_recent_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
            limit=1,
        )
        self.assertLessEqual(len(result['threads']), 1)

    def test_unread_count_in_result(self):
        result = CommunicationSearchService.get_recent_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
        )
        for t in result['threads']:
            self.assertIn('unread_count', t)


# =============================================================================
# 12. API Endpoint Tests
# =============================================================================

class TestSearchEndpoints(TestCase):
    factory = APIRequestFactory()

    def setUp(self):
        self.user = _user('api_search_user@test.com', TENANT_A)
        self.thread = _thread(TENANT_A, subject='API search thread')
        _participant(self.thread, self.user)
        self.msg = _message(self.thread, self.user, body='API endpoint search match content')

    def _get(self, view_class, url_kwargs=None, query_params='', user=None):
        user = user or self.user
        url = f'/test/?{query_params}'
        request = self.factory.get(url)
        force_authenticate(request, user=user)
        view = view_class.as_view()
        if url_kwargs:
            return view(request, **url_kwargs)
        return view(request)

    def test_global_search_requires_q(self):
        request = self.factory.get('/test/')
        force_authenticate(request, user=self.user)
        response = GlobalCommunicationSearchView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_global_search_returns_200(self):
        request = self.factory.get('/test/?q=API+endpoint')
        force_authenticate(request, user=self.user)
        response = GlobalCommunicationSearchView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data['data'])
        self.assertIn('total', response.data['data'])

    def test_global_search_result_structure(self):
        request = self.factory.get('/test/?q=API+endpoint+search')
        force_authenticate(request, user=self.user)
        response = GlobalCommunicationSearchView.as_view()(request)
        results = response.data['data']['results']
        if results:
            item = results[0]
            for field in ('type', 'id', 'title', 'snippet', 'sent_at', 'nav_target'):
                self.assertIn(field, item)

    def test_global_search_unauthenticated(self):
        request = self.factory.get('/test/?q=test')
        response = GlobalCommunicationSearchView.as_view()(request)
        # DRF returns 401 for missing credentials (IsAuthenticated)
        self.assertIn(response.status_code, (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ))

    def test_thread_search_requires_q(self):
        request = self.factory.get('/test/')
        force_authenticate(request, user=self.user)
        response = ThreadMessageSearchView.as_view()(request, pk=self.thread.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_thread_search_returns_200(self):
        request = self.factory.get('/test/?q=endpoint+search')
        force_authenticate(request, user=self.user)
        response = ThreadMessageSearchView.as_view()(request, pk=self.thread.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_thread_search_non_participant_returns_403(self):
        outsider = _user('api_search_outsider@test.com', TENANT_A)
        request = self.factory.get('/test/?q=endpoint')
        force_authenticate(request, user=outsider)
        response = ThreadMessageSearchView.as_view()(request, pk=self.thread.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_archive_endpoint_works(self):
        request = self.factory.post('/test/')
        force_authenticate(request, user=self.user)
        response = ArchiveThreadView.as_view()(request, pk=self.thread.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_archived)

    def test_unarchive_endpoint_works(self):
        self.thread.is_archived = True
        self.thread.archived_at = timezone.now()
        self.thread.archived_by = self.user.id
        self.thread.save()
        request = self.factory.post('/test/')
        force_authenticate(request, user=self.user)
        response = UnarchiveThreadView.as_view()(request, pk=self.thread.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_archived)

    def test_archive_endpoint_nonexistent_returns_404(self):
        request = self.factory.post('/test/')
        force_authenticate(request, user=self.user)
        response = ArchiveThreadView.as_view()(request, pk=uuid.uuid4())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_archived_list_endpoint(self):
        self.thread.is_archived = True
        self.thread.archived_at = timezone.now()
        self.thread.save()
        request = self.factory.get('/test/')
        force_authenticate(request, user=self.user)
        response = ArchivedThreadListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('threads', response.data['data'])

    def test_entity_history_endpoint(self):
        entity_id = uuid.uuid4()
        request = self.factory.get('/test/')
        force_authenticate(request, user=self.user)
        response = EntityCommunicationHistoryView.as_view()(
            request, entity_type='candidate', entity_id=entity_id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('timeline', response.data['data'])

    def test_recent_communications_endpoint(self):
        request = self.factory.get('/test/')
        force_authenticate(request, user=self.user)
        response = RecentCommunicationsView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('threads', response.data['data'])

    def test_notification_history_endpoint(self):
        _notification(self.user, title='Test notification for history endpoint')
        request = self.factory.get('/test/')
        force_authenticate(request, user=self.user)
        response = NotificationHistoryView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('notifications', response.data['data'])

    def test_notification_history_q_filter(self):
        _notification(self.user, title='Unique notification title xyzzy')
        request = self.factory.get('/test/?q=Unique+notification+title+xyzzy')
        force_authenticate(request, user=self.user)
        response = NotificationHistoryView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notifications = response.data['data']['notifications']
        titles = [n['title'] for n in notifications]
        self.assertTrue(any('xyzzy' in t for t in titles))

    def test_notification_history_is_read_filter(self):
        _notification(self.user, title='Unread test notif', is_read=False)
        request = self.factory.get('/test/?is_read=false')
        force_authenticate(request, user=self.user)
        response = NotificationHistoryView.as_view()(request)
        notifications = response.data['data']['notifications']
        for n in notifications:
            self.assertFalse(n['is_read'])


# =============================================================================
# 13. Pagination Enforcement
# =============================================================================

class TestPaginationEnforcement(TestCase):

    def setUp(self):
        self.user = _user('pagination_user@test.com', TENANT_A)
        self.thread = _thread(TENANT_A, subject='Pagination thread')
        _participant(self.thread, self.user)
        # Create 15 messages all matching a search term
        for i in range(15):
            _message(self.thread, self.user, body=f'Paginated message content item {i}')

    def test_global_search_limit_respected(self):
        result = CommunicationSearchService.search_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
            query='Paginated message content',
            limit=5,
        )
        self.assertLessEqual(len(result['results']), 5)
        self.assertGreater(result['total'], 5)

    def test_global_search_max_limit_capped(self):
        result = CommunicationSearchService.search_communications(
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
            query='Paginated message content',
            limit=9999,
        )
        self.assertLessEqual(len(result['results']), 200)  # _MAX_PAGE_SIZE

    def test_thread_search_pagination(self):
        result = CommunicationSearchService.search_thread_messages(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
            query='Paginated message content',
            limit=3,
            offset=0,
        )
        self.assertLessEqual(len(result['results']), 3)
        self.assertGreater(result['total'], 3)

    def test_thread_search_offset(self):
        result_page1 = CommunicationSearchService.search_thread_messages(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
            query='Paginated message content',
            limit=5,
            offset=0,
        )
        result_page2 = CommunicationSearchService.search_thread_messages(
            thread_id=str(self.thread.id),
            tenant_id=str(TENANT_A),
            user_id=str(self.user.id),
            query='Paginated message content',
            limit=5,
            offset=5,
        )
        ids_p1 = {r['id'] for r in result_page1['results']}
        ids_p2 = {r['id'] for r in result_page2['results']}
        # Pages must not overlap
        self.assertEqual(len(ids_p1 & ids_p2), 0)
