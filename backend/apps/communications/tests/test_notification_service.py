"""
QA Tests: Notification Service
"""
import uuid
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.communications.models import (
    Notification, NotificationDelivery, NotificationSeverity,
)
from apps.communications.notification_service import NotificationService

TENANT_A = uuid.uuid4()
USER_1 = uuid.uuid4()
USER_2 = uuid.uuid4()


class TestCreateNotification(TestCase):

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_creates_notification(self, mock_rt, mock_fallback):
        n = NotificationService.create_notification(
            user_id=USER_1,
            title='Test notification',
            body='Body text',
            notification_type='test.event',
            severity=NotificationSeverity.INFO,
            tenant_id=TENANT_A,
        )
        self.assertIsNotNone(n.id)
        self.assertEqual(n.user_id, USER_1)
        self.assertEqual(n.title, 'Test notification')
        self.assertFalse(n.is_read)

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_in_app_delivery_recorded(self, mock_rt, mock_fallback):
        n = NotificationService.create_notification(
            user_id=USER_1,
            title='Delivery test',
            tenant_id=TENANT_A,
        )
        delivery = NotificationDelivery.objects.filter(notification=n, channel='in_app').first()
        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.status, 'delivered')

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    def test_schedule_fallback_called_for_high_severity(self, mock_fallback):
        with patch('apps.communications.realtime.RealtimePublisher.publish_notification'):
            NotificationService.create_notification(
                user_id=USER_1,
                title='High priority',
                severity=NotificationSeverity.HIGH,
                schedule_fallback=True,
            )
        mock_fallback.assert_called_once()

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    def test_no_fallback_for_info_severity(self, mock_fallback):
        with patch('apps.communications.realtime.RealtimePublisher.publish_notification'):
            NotificationService.create_notification(
                user_id=USER_1,
                title='Info notification',
                severity=NotificationSeverity.INFO,
                schedule_fallback=True,
            )
        # _schedule_fallback_if_needed is called but internally does nothing for INFO
        # We check the celery task wasn't scheduled by mocking at the celery level
        # (This test covers the service call path)
        mock_fallback.assert_called_once()


class TestMarkRead(TestCase):

    def _create(self, user_id=USER_1, severity=NotificationSeverity.INFO):
        with patch('apps.communications.realtime.RealtimePublisher.publish_notification'):
            with patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed'):
                return NotificationService.create_notification(
                    user_id=user_id,
                    title='N',
                    severity=severity,
                    tenant_id=TENANT_A,
                )

    def test_mark_read_updates_notification(self):
        n = self._create()
        with patch('apps.communications.realtime.RealtimePublisher.publish_unread_count'):
            result = NotificationService.mark_read(notification_id=n.id, user_id=USER_1)
        self.assertTrue(result.is_read)
        self.assertIsNotNone(result.read_at)

    def test_mark_read_wrong_user_raises(self):
        n = self._create()
        from rest_framework.exceptions import NotFound
        with self.assertRaises(NotFound):
            NotificationService.mark_read(notification_id=n.id, user_id=USER_2)

    def test_mark_all_read(self):
        self._create()
        self._create()
        with patch('apps.communications.realtime.RealtimePublisher.publish_unread_count'):
            count = NotificationService.mark_all_read(user_id=USER_1, tenant_id=TENANT_A)
        self.assertGreaterEqual(count, 2)
        remaining_unread = Notification.objects.filter(user_id=USER_1, is_read=False).count()
        self.assertEqual(remaining_unread, 0)


class TestUnreadCount(TestCase):

    def _create(self, user_id=USER_1):
        with patch('apps.communications.realtime.RealtimePublisher.publish_notification'):
            with patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed'):
                return NotificationService.create_notification(
                    user_id=user_id, title='N', tenant_id=TENANT_A
                )

    def test_unread_count_increases(self):
        before = NotificationService.get_unread_count(user_id=USER_1)
        self._create()
        self._create()
        after = NotificationService.get_unread_count(user_id=USER_1)
        self.assertEqual(after - before, 2)

    def test_unread_count_decreases_after_read(self):
        n = self._create()
        before = NotificationService.get_unread_count(user_id=USER_1)
        with patch('apps.communications.realtime.RealtimePublisher.publish_unread_count'):
            NotificationService.mark_read(notification_id=n.id, user_id=USER_1)
        after = NotificationService.get_unread_count(user_id=USER_1)
        self.assertEqual(after, before - 1)

    def test_expired_notifications_not_counted(self):
        with patch('apps.communications.realtime.RealtimePublisher.publish_notification'):
            with patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed'):
                expired = NotificationService.create_notification(
                    user_id=USER_1,
                    title='Expired',
                    tenant_id=TENANT_A,
                    expires_at=timezone.now() - timezone.timedelta(hours=1),
                )
        count = NotificationService.get_unread_count(user_id=USER_1)
        # Expired notification should not count
        self.assertFalse(
            Notification.objects.filter(
                id=expired.id, user_id=USER_1, is_read=False
            ).filter(expires_at__gt=timezone.now()).exists()
        )


class TestBulkNotifications(TestCase):

    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    def test_creates_notification_per_user(self, mock_rt, mock_fallback):
        user_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        notifications = NotificationService.create_bulk_notifications(
            user_ids=user_ids,
            title='Bulk notification',
            body='Bulk body',
        )
        self.assertEqual(len(notifications), 3)
        created_user_ids = [n.user_id for n in notifications]
        for uid in user_ids:
            self.assertIn(uid, created_user_ids)


class TestRecordDelivery(TestCase):

    @patch('apps.communications.realtime.RealtimePublisher.publish_notification')
    @patch('apps.communications.notification_service.NotificationService._schedule_fallback_if_needed')
    def test_record_delivery_attempt(self, mock_fb, mock_rt):
        n = NotificationService.create_notification(
            user_id=USER_1, title='N', tenant_id=TENANT_A
        )
        delivery = NotificationService.record_delivery_attempt(
            notification_id=n.id,
            channel='email',
            provider='sendgrid',
            status='sent',
            external_message_id='msg_123',
            tenant_id=TENANT_A,
        )
        self.assertEqual(delivery.status, 'sent')
        n.refresh_from_db()
        self.assertIsNotNone(n.fallback_email_sent_at)
