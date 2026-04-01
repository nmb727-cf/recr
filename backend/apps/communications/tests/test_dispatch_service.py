import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.communications.email_dispatch.types import EmailSendRequest
from apps.communications.services import CommunicationDispatchService
from apps.communications.models import Notification
from shared.owner_contracts import OwnerActionContext, OwnerContractError


class CommunicationDispatchServiceTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.other_tenant_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        self.user = get_user_model().objects.create_user(
            email='notify-owner@example.com',
            password='testpass123',
            tenant_id=self.tenant_id,
            role='recruiter',
        )
        self.other_user = get_user_model().objects.create_user(
            email='notify-other@example.com',
            password='testpass123',
            tenant_id=self.other_tenant_id,
            role='recruiter',
        )
        self.user_id = self.user.id

    def test_dispatch_notification_is_idempotent_by_dedupe_key(self):
        created, count = CommunicationDispatchService.dispatch_notification(
            tenant_id=self.tenant_id,
            actor_user_id=self.user_id,
            recipient_user_ids=[self.user_id],
            title='Reminder',
            body='Pending action.',
            notification_type='reminder_notification',
            dedupe_key='notify-dedupe',
        )
        duplicate, duplicate_count = CommunicationDispatchService.dispatch_notification(
            tenant_id=self.tenant_id,
            actor_user_id=self.user_id,
            recipient_user_ids=[self.user_id],
            title='Reminder',
            body='Pending action.',
            notification_type='reminder_notification',
            dedupe_key='notify-dedupe',
        )

        self.assertEqual(count, 1)
        self.assertEqual(duplicate_count, 0)
        self.assertEqual(created[0].id, duplicate[0].id)
        self.assertEqual(
            Notification.objects.filter(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                notification_type='reminder_notification',
                metadata__orchestration_dedupe_key='notify-dedupe',
            ).count(),
            1,
        )

    def test_queue_email_uses_email_dispatch_service(self):
        request = EmailSendRequest(
            tenant_id=str(self.tenant_id),
            actor_user_id=str(self.user_id),
            email_type='business',
            message_purpose='followup',
            recipients=['candidate@example.com'],
            subject='Follow up',
            body_text='Hello',
        )
        with patch('apps.communications.services.EmailDispatchService.queue_send') as queue_send:
            CommunicationDispatchService.queue_email(request)

        queue_send.assert_called_once_with(request)

    def test_notify_from_orchestration_returns_duplicate_result_on_retry(self):
        context = OwnerActionContext(
            tenant_id=self.tenant_id,
            actor_id=self.user_id,
            external_reference='notify-contract-dedupe',
            audit_metadata={'automation_run_id': 'run-1'},
        )

        first = CommunicationDispatchService.notify_from_orchestration(
            context=context,
            recipient_user_ids=[self.user_id],
            title='Reminder',
            body='Pending action.',
            notification_type='reminder_notification',
            dedupe_key='notify-contract-dedupe',
            notification_style='reminder',
        )
        second = CommunicationDispatchService.notify_from_orchestration(
            context=context,
            recipient_user_ids=[self.user_id],
            title='Reminder',
            body='Pending action.',
            notification_type='reminder_notification',
            dedupe_key='notify-contract-dedupe',
            notification_style='reminder',
        )

        self.assertFalse(first.duplicate)
        self.assertTrue(second.duplicate)
        self.assertEqual(second.execution_status(), 'deduplicated')
        self.assertEqual(second.payload['recipient_count'], 1)

    def test_notify_from_orchestration_rejects_cross_tenant_recipient(self):
        with self.assertRaises(OwnerContractError) as exc_info:
            CommunicationDispatchService.notify_from_orchestration(
                context=OwnerActionContext(
                    tenant_id=self.tenant_id,
                    actor_id=self.user_id,
                    external_reference='notify-contract-ownership',
                    audit_metadata={'automation_run_id': 'run-1'},
                ),
                recipient_user_ids=[self.other_user.id],
                title='Reminder',
                body='Pending action.',
                notification_type='reminder_notification',
                dedupe_key='notify-contract-ownership',
            )

        self.assertEqual(exc_info.exception.error_category, OwnerContractError.CATEGORY_OWNERSHIP)
