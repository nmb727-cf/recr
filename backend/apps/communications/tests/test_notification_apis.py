"""
QA Tests: Notification API Endpoints
Uses APIRequestFactory + direct view calls to bypass django-tenants middleware.
"""
import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.communications.models import Notification, NotificationSeverity
from apps.communications.notification_service import NotificationService
from apps.communications.views import (
    NotificationListView,
    NotificationUnreadCountView,
    NotificationReadView,
    NotificationReadAllView,
)

TENANT_A = uuid.UUID('00000000-0000-0000-0000-000000000003')


def _user(email, tenant_id=TENANT_A):
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return CustomUser.objects.create_user(
            email=email, password='testpass123', role='recruiter', tenant_id=tenant_id,
        )


def _create_notification(user_id, severity=NotificationSeverity.INFO, is_read=False, tenant_id=TENANT_A):
    with patch('apps.communications.realtime.RealtimePublisher.publish_notification'):
        with patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed'):
            n = NotificationService.create_notification(
                user_id=user_id,
                title='Test notification',
                body='Body',
                severity=severity,
                tenant_id=tenant_id,
            )
    if is_read:
        with patch('apps.communications.realtime.RealtimePublisher.publish_unread_count'):
            NotificationService.mark_read(notification_id=n.id, user_id=user_id)
    return n


class TestNotificationList(TestCase):
    factory = APIRequestFactory()

    def setUp(self):
        self.user = _user('notif_list_user@test.com')

    def test_list_all_notifications(self):
        _create_notification(self.user.id)
        _create_notification(self.user.id)
        request = self.factory.get('/notifications/')
        force_authenticate(request, user=self.user)
        response = NotificationListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['data']['notifications']), 2)

    def test_filter_unread_notifications(self):
        _create_notification(self.user.id, is_read=False)
        _create_notification(self.user.id, is_read=True)
        request = self.factory.get('/notifications/?is_read=false')
        force_authenticate(request, user=self.user)
        response = NotificationListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for n in response.data['data']['notifications']:
            self.assertFalse(n['is_read'])

    def test_filter_read_notifications(self):
        _create_notification(self.user.id, is_read=True)
        request = self.factory.get('/notifications/?is_read=true')
        force_authenticate(request, user=self.user)
        response = NotificationListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for n in response.data['data']['notifications']:
            self.assertTrue(n['is_read'])

    def test_meta_includes_unread_count(self):
        _create_notification(self.user.id, is_read=False)
        request = self.factory.get('/notifications/')
        force_authenticate(request, user=self.user)
        response = NotificationListView.as_view()(request)
        self.assertIn('unread', response.data['meta'])
        self.assertGreaterEqual(response.data['meta']['unread'], 1)

    def test_unauthenticated_rejected(self):
        request = self.factory.get('/notifications/')
        response = NotificationListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_other_user_cannot_see_my_notifications(self):
        _create_notification(self.user.id)
        other_user = _user('other_notif@test.com')
        request = self.factory.get('/notifications/')
        force_authenticate(request, user=other_user)
        response = NotificationListView.as_view()(request)
        my_notification_ids = set(
            str(n.id) for n in Notification.objects.filter(user_id=self.user.id)
        )
        returned_ids = {n['id'] for n in response.data['data']['notifications']}
        self.assertTrue(my_notification_ids.isdisjoint(returned_ids))


class TestNotificationUnreadCount(TestCase):
    factory = APIRequestFactory()

    def setUp(self):
        self.user = _user('unread_count_user@test.com')

    def test_unread_count_endpoint(self):
        _create_notification(self.user.id)
        _create_notification(self.user.id)
        request = self.factory.get('/notifications/unread-count/')
        force_authenticate(request, user=self.user)
        response = NotificationUnreadCountView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('unread_count', response.data['data'])
        self.assertGreaterEqual(response.data['data']['unread_count'], 2)

    def test_unread_count_is_zero_after_mark_all_read(self):
        _create_notification(self.user.id)
        with patch('apps.communications.realtime.RealtimePublisher.publish_unread_count'):
            NotificationService.mark_all_read(user_id=self.user.id)
        request = self.factory.get('/notifications/unread-count/')
        force_authenticate(request, user=self.user)
        response = NotificationUnreadCountView.as_view()(request)
        self.assertEqual(response.data['data']['unread_count'], 0)


class TestMarkNotificationRead(TestCase):
    factory = APIRequestFactory()

    def setUp(self):
        self.user = _user('mark_read_user@test.com')

    def test_mark_notification_read(self):
        n = _create_notification(self.user.id)
        request = self.factory.post(f'/notifications/{n.id}/mark-read/')
        force_authenticate(request, user=self.user)
        with patch('apps.communications.realtime.RealtimePublisher.publish_unread_count'):
            response = NotificationReadView.as_view()(request, pk=n.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        n.refresh_from_db()
        self.assertTrue(n.is_read)
        self.assertIsNotNone(n.read_at)

    def test_mark_other_user_notification_fails(self):
        other_user = _user('other_mark_read@test.com')
        n = _create_notification(other_user.id)
        request = self.factory.post(f'/notifications/{n.id}/mark-read/')
        force_authenticate(request, user=self.user)
        with patch('apps.communications.realtime.RealtimePublisher.publish_unread_count'):
            response = NotificationReadView.as_view()(request, pk=n.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_nonexistent_notification_read(self):
        fake_id = uuid.uuid4()
        request = self.factory.post(f'/notifications/{fake_id}/mark-read/')
        force_authenticate(request, user=self.user)
        response = NotificationReadView.as_view()(request, pk=fake_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_idempotent_mark_read(self):
        n = _create_notification(self.user.id)
        for _ in range(2):
            request = self.factory.post(f'/notifications/{n.id}/mark-read/')
            force_authenticate(request, user=self.user)
            with patch('apps.communications.realtime.RealtimePublisher.publish_unread_count'):
                response = NotificationReadView.as_view()(request, pk=n.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestMarkAllRead(TestCase):
    factory = APIRequestFactory()

    def setUp(self):
        self.user = _user('mark_all_read_user@test.com')

    def test_mark_all_read(self):
        for _ in range(3):
            _create_notification(self.user.id)
        request = self.factory.post('/notifications/mark-all-read/')
        force_authenticate(request, user=self.user)
        with patch('apps.communications.realtime.RealtimePublisher.publish_unread_count'):
            response = NotificationReadAllView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        remaining_unread = Notification.objects.filter(user_id=self.user.id, is_read=False).count()
        self.assertEqual(remaining_unread, 0)

    def test_unauthenticated_rejected(self):
        request = self.factory.post('/notifications/mark-all-read/')
        response = NotificationReadAllView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_updated_count(self):
        for _ in range(2):
            _create_notification(self.user.id)
        request = self.factory.post('/notifications/mark-all-read/')
        force_authenticate(request, user=self.user)
        with patch('apps.communications.realtime.RealtimePublisher.publish_unread_count'):
            response = NotificationReadAllView.as_view()(request)
        self.assertIn('updated_count', response.data['data'])
        self.assertGreaterEqual(response.data['data']['updated_count'], 2)
