import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowActorAssignment,
    WorkflowInstance,
    WorkflowNotificationLog,
    WorkflowNotificationQueue,
    WorkflowNotificationRule,
    WorkflowSLAEvent,
    WorkflowStageExecution,
    WorkflowStageSLA,
)
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_notification_engine import WorkflowNotificationEngine
from apps.workflow_execution.services.workflow_sla_engine import WorkflowSLAEngine


@pytest.mark.django_db
class TestWorkflowNotificationEngine:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        self.workflow_id = uuid.uuid4()
        self.stage_id = uuid.uuid4()
        self.actor_id = uuid.uuid4()
        self.owner_id = uuid.uuid4()
        self.candidate_id = uuid.uuid4()

        self.instance = WorkflowInstance.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow_id,
            entity_type='candidate',
            entity_id=self.candidate_id,
            status='running',
            context_data={
                'workflow_name': 'Hiring Workflow',
                'workflow_owner_id': str(self.owner_id),
                'candidate_id': str(self.candidate_id),
                'job_title': 'Senior Engineer',
            },
        )

    def test_1_stage_starts_queues_notification_for_assigned_actor(self):
        WorkflowNotificationRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow_id,
            stage_id=self.stage_id,
            trigger_type='stage_started',
            recipient_type='assigned_actor',
            channel='in_app',
            template_key='workflow_stage_started',
            is_active=True,
        )
        WorkflowActorAssignment.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_id=self.stage_id,
            actor_type='recruiter',
            actor_id=self.actor_id,
            assignment_type='responsible',
            status='active',
        )

        WorkflowInstanceTracker.start_stage_execution(
            self.instance,
            stage_id=self.stage_id,
            stage_name='candidate_review',
            actor_type='system',
        )
        queue_item = WorkflowNotificationQueue.objects.filter(
            workflow_instance=self.instance,
            recipient_type='assigned_actor',
            template_key='workflow_stage_started',
        ).first()
        assert queue_item is not None
        assert str(queue_item.recipient_id) == str(self.actor_id)

    def test_2_sla_warning_triggered_notification_sent(self):
        WorkflowNotificationRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow_id,
            stage_id=self.stage_id,
            trigger_type='sla_warning',
            recipient_type='workflow_owner',
            channel='email',
            template_key='workflow_sla_warning',
            is_active=True,
        )
        stage_execution = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_id=self.stage_id,
            stage_name='interview_schedule',
            status='running',
        )
        WorkflowStageSLA.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow_id,
            stage_id=self.stage_id,
            sla_duration=timedelta(hours=24),
            warning_duration=timedelta(hours=12),
            escalation_duration=timedelta(hours=24),
            escalation_role='hiring_manager',
            is_active=True,
        )
        tracker = WorkflowSLAEngine.initialize_sla(self.instance, stage_execution)
        tracker.warning_at = timezone.now() - timedelta(minutes=2)
        tracker.breach_at = timezone.now() + timedelta(hours=3)
        tracker.save(update_fields=['warning_at', 'breach_at', 'updated_at'])

        events = WorkflowSLAEngine.check_sla_status(tracker=tracker)
        assert any(event['event'] == 'warning' for event in events)
        assert WorkflowSLAEvent.objects.filter(workflow_instance=self.instance, event_type='warning').exists()

        WorkflowNotificationEngine.process_notification_queue(limit=50)
        assert WorkflowNotificationLog.objects.filter(
            workflow_instance=self.instance,
            template_key='workflow_sla_warning',
            status='sent',
        ).exists()

    def test_3_workflow_failed_notification_sent_to_responsible_users(self):
        WorkflowNotificationRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow_id,
            stage_id=self.stage_id,
            trigger_type='workflow_failed',
            recipient_type='assigned_actor',
            channel='in_app',
            template_key='workflow_failure',
            is_active=True,
        )
        stage_execution = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_id=self.stage_id,
            stage_name='offer_approval',
            status='running',
        )
        WorkflowActorAssignment.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_id=self.stage_id,
            actor_type='hiring_manager',
            actor_id=self.actor_id,
            assignment_type='responsible',
            status='active',
        )

        WorkflowInstanceTracker.log_failure(
            self.instance,
            stage_execution=stage_execution,
            error_message='Approval timeout',
            error_type='timeout',
            retry_count=0,
            status='failed',
        )
        WorkflowNotificationEngine.process_notification_queue(limit=50)

        assert WorkflowNotificationLog.objects.filter(
            workflow_instance=self.instance,
            template_key='workflow_failure',
            status='sent',
        ).exists()

    def test_4_candidate_related_stage_resolves_candidate_recipient(self):
        WorkflowNotificationRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow_id,
            stage_id=self.stage_id,
            trigger_type='stage_started',
            recipient_type='candidate',
            channel='email',
            template_key='workflow_stage_started',
            is_active=True,
        )
        WorkflowInstanceTracker.start_stage_execution(
            self.instance,
            stage_id=self.stage_id,
            stage_name='candidate_confirmation',
            actor_type='system',
        )

        queue_item = WorkflowNotificationQueue.objects.filter(
            workflow_instance=self.instance,
            recipient_type='candidate',
            template_key='workflow_stage_started',
        ).first()
        assert queue_item is not None
        assert str(queue_item.recipient_id) == str(self.candidate_id)

    def test_5_template_rendering_logs_message_preview(self):
        WorkflowNotificationRule.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow_id,
            stage_id=self.stage_id,
            trigger_type='stage_completed',
            recipient_type='workflow_owner',
            channel='in_app',
            template_key='workflow_stage_completed',
            is_active=True,
        )
        stage_execution = WorkflowInstanceTracker.start_stage_execution(
            self.instance,
            stage_id=self.stage_id,
            stage_name='offer_stage',
            actor_type='system',
        )
        WorkflowInstanceTracker.complete_stage_execution(stage_execution, actor_type='system')
        WorkflowNotificationEngine.process_notification_queue(limit=50)

        log = WorkflowNotificationLog.objects.filter(
            workflow_instance=self.instance,
            template_key='workflow_stage_completed',
            status='sent',
        ).order_by('-created_at').first()
        assert log is not None
        assert 'Stage completed' in log.message_preview
