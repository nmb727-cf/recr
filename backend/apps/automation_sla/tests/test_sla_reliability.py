import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.automation_sla.models import (
    SLAReminderStatus,
    SLAReminderType,
    SLAExecutionStatus,
    WorkflowSLAPolicy,
    WorkflowSLAReminder,
)
from apps.automation_sla.services.workflow_sla_engine import WorkflowSLAEngine
from apps.automation_sla.tasks import check_sla_reminders


class WorkflowSLAReliabilityTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.entity_id = str(uuid.uuid4())
        self.policy = WorkflowSLAPolicy.objects.create(
            tenant_id=self.tenant_id,
            name='Pipeline Review SLA',
            module_scope='pipeline',
            trigger_event='application.created',
            entity_type='application',
            deadline_minutes=120,
            warning_before_minutes=60,
            escalation_after_minutes=90,
            priority='medium',
            is_active=True,
        )

    def test_create_sla_execution_is_idempotent_for_active_execution(self):
        first = WorkflowSLAEngine.create_sla_execution(
            tenant_id=self.tenant_id,
            policy=self.policy,
            entity_type='application',
            entity_id=self.entity_id,
        )
        second = WorkflowSLAEngine.create_sla_execution(
            tenant_id=self.tenant_id,
            policy=self.policy,
            entity_type='application',
            entity_id=self.entity_id,
        )
        self.assertEqual(first.id, second.id)

    def test_schedule_warning_reminder_does_not_duplicate(self):
        execution = WorkflowSLAEngine.create_sla_execution(
            tenant_id=self.tenant_id,
            policy=self.policy,
            entity_type='application',
            entity_id=self.entity_id,
        )
        WorkflowSLAEngine.schedule_warning_reminder(execution)
        count = WorkflowSLAReminder.objects.filter(
            sla_execution=execution,
            reminder_type=SLAReminderType.WARNING,
        ).count()
        self.assertEqual(count, 1)

    def test_check_sla_reminders_skips_completed_execution(self):
        execution = WorkflowSLAEngine.create_sla_execution(
            tenant_id=self.tenant_id,
            policy=self.policy,
            entity_type='application',
            entity_id=self.entity_id,
        )
        execution.current_status = SLAExecutionStatus.COMPLETED
        execution.completed_at = timezone.now()
        execution.save(update_fields=['current_status', 'completed_at', 'updated_at'])

        reminder = WorkflowSLAReminder.objects.create(
            tenant_id=self.tenant_id,
            sla_execution=execution,
            reminder_type=SLAReminderType.WARNING,
            recipient_type='owner',
            scheduled_at=timezone.now() - timedelta(minutes=1),
            status=SLAReminderStatus.SCHEDULED,
        )

        check_sla_reminders()
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, SLAReminderStatus.SKIPPED)

    def test_cancel_sla_cancels_scheduled_reminders(self):
        execution = WorkflowSLAEngine.create_sla_execution(
            tenant_id=self.tenant_id,
            policy=self.policy,
            entity_type='application',
            entity_id=self.entity_id,
        )
        WorkflowSLAReminder.objects.create(
            tenant_id=self.tenant_id,
            sla_execution=execution,
            reminder_type=SLAReminderType.ESCALATION,
            recipient_type='admin',
            scheduled_at=timezone.now() + timedelta(minutes=30),
            status=SLAReminderStatus.SCHEDULED,
        )

        WorkflowSLAEngine.cancel_sla(
            tenant_id=self.tenant_id,
            entity_type='application',
            entity_id=self.entity_id,
        )
        reminder_statuses = list(
            WorkflowSLAReminder.objects.filter(sla_execution=execution).values_list('status', flat=True)
        )
        self.assertTrue(reminder_statuses)
        self.assertTrue(all(status == SLAReminderStatus.CANCELLED for status in reminder_statuses))

