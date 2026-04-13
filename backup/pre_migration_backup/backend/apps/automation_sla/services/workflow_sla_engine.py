import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from apps.automation_sla.models import (
    WorkflowSLAPolicy,
    WorkflowSLAExecution,
    WorkflowSLAReminder,
    WorkflowSLAEscalationRule,
    WorkflowSLABreachInsight,
    SLAExecutionStatus,
    SLAReminderType,
    SLAReminderStatus,
    SLABreachInsightType,
)

logger = logging.getLogger(__name__)

class WorkflowSLAEngine:

    @staticmethod
    @transaction.atomic
    def create_sla_execution(tenant_id, policy: WorkflowSLAPolicy, entity_type, entity_id, workflow_id=None, owner_id=None, metadata=None):
        """
        Entry point to start tracking an SLA for an entity.
        """
        now = timezone.now()
        due_at = now + timedelta(minutes=policy.deadline_minutes)
        warning_at = due_at - timedelta(minutes=policy.warning_before_minutes)

        execution = WorkflowSLAExecution.objects.create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            sla_policy=policy,
            entity_type=entity_type,
            entity_id=entity_id,
            owner_user_id=owner_id,
            current_status=SLAExecutionStatus.ACTIVE,
            started_at=now,
            due_at=due_at,
            warning_at=warning_at,
            metadata=metadata or {}
        )

        # Schedule warning reminder
        WorkflowSLAEngine.schedule_warning_reminder(execution)
        
        logger.info(f"SLA Execution created: {execution.id} for {entity_type}:{entity_id}")
        return execution

    @staticmethod
    def schedule_warning_reminder(execution: WorkflowSLAExecution):
        if not execution.warning_at or execution.warning_at < timezone.now():
            return

        WorkflowSLAReminder.objects.create(
            tenant_id=execution.tenant_id,
            sla_execution=execution,
            reminder_type=SLAReminderType.WARNING,
            recipient_type='owner',
            scheduled_at=execution.warning_at,
            status=SLAReminderStatus.SCHEDULED
        )

    @staticmethod
    @transaction.atomic
    def detect_breach(tenant_id=None):
        """
        Scans active SLAs and marks them as breached if due_at is passed.
        Can be filtered by tenant_id for targeted processing.
        """
        now = timezone.now()
        filters = {'current_status__in': [SLAExecutionStatus.ACTIVE, SLAExecutionStatus.WARNING_DUE], 'due_at__lt': now}
        if tenant_id:
            filters['tenant_id'] = tenant_id

        breached_executions = WorkflowSLAExecution.objects.filter(**filters)
        results = []

        for execution in breached_executions:
            execution.current_status = SLAExecutionStatus.BREACHED
            execution.breached_at = now
            execution.save(update_fields=['current_status', 'breached_at', 'updated_at'])
            
            # Trigger first level escalation immediately
            WorkflowSLAEngine.process_escalation(execution)
            results.append(str(execution.id))

        return results

    @staticmethod
    @transaction.atomic
    def process_escalation(execution: WorkflowSLAExecution):
        """
        Handles multi-level escalation for a breached SLA.
        """
        next_level = execution.escalation_level + 1
        rule = WorkflowSLAEscalationRule.objects.filter(
            sla_policy=execution.sla_policy,
            escalation_level=next_level,
            is_active=True
        ).first()

        if rule:
            execution.escalation_level = next_level
            execution.current_status = SLAExecutionStatus.ESCALATED
            execution.save(update_fields=['escalation_level', 'current_status', 'updated_at'])
            
            # Create escalation reminder/notification
            WorkflowSLAReminder.objects.create(
                tenant_id=execution.tenant_id,
                sla_execution=execution,
                reminder_type=SLAReminderType.ESCALATION,
                recipient_type=rule.target_role or 'admin',
                scheduled_at=timezone.now(),
                status=SLAReminderStatus.SCHEDULED
            )
            
            logger.info(f"SLA {execution.id} escalated to Level {next_level}")
            return True
        
        return False

    @staticmethod
    @transaction.atomic
    def complete_sla(tenant_id, entity_type, entity_id, policy_name=None):
        """
        Marks an SLA as completed when the target action is performed.
        """
        now = timezone.now()
        filters = {
            'tenant_id': tenant_id,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'current_status__in': [SLAExecutionStatus.ACTIVE, SLAExecutionStatus.WARNING_DUE, SLAExecutionStatus.BREACHED, SLAExecutionStatus.ESCALATED]
        }
        if policy_name:
            filters['sla_policy__name'] = policy_name

        executions = WorkflowSLAExecution.objects.filter(**filters)
        for execution in executions:
            execution.current_status = SLAExecutionStatus.COMPLETED
            execution.completed_at = now
            execution.save(update_fields=['current_status', 'completed_at', 'updated_at'])
            
            # Cancel all pending reminders
            WorkflowSLAReminder.objects.filter(
                sla_execution=execution,
                status=SLAReminderStatus.SCHEDULED
            ).update(status=SLAReminderStatus.CANCELLED)

        return executions.count()

    @staticmethod
    @transaction.atomic
    def cancel_sla(tenant_id, entity_type, entity_id):
        """
        Cancels tracking if the entity is no longer relevant.
        """
        executions = WorkflowSLAExecution.objects.filter(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            current_status__in=[SLAExecutionStatus.ACTIVE, SLAExecutionStatus.WARNING_DUE, SLAExecutionStatus.BREACHED, SLAExecutionStatus.ESCALATED]
        )
        count = executions.count()
        executions.update(current_status=SLAExecutionStatus.CANCELLED, updated_at=timezone.now())
        return count

    @staticmethod
    def generate_breach_insights(tenant_id):
        """
        Analyzes performance and generates proactive insights.
        """
        from django.db.models import Count
        
        # Simple insight: Frequent breaches on a specific policy
        policies_with_breaches = WorkflowSLAExecution.objects.filter(
            tenant_id=tenant_id,
            current_status__in=[SLAExecutionStatus.BREACHED, SLAExecutionStatus.ESCALATED]
        ).values('sla_policy').annotate(breach_count=Count('id')).filter(breach_count__gt=5)

        insights_created = 0
        for item in policies_with_breaches:
            policy = WorkflowSLAPolicy.objects.get(id=item['sla_policy'])
            insight, created = WorkflowSLABreachInsight.objects.get_or_create(
                tenant_id=tenant_id,
                sla_policy=policy,
                insight_type=SLABreachInsightType.REPEATED_BREACH,
                defaults={
                    'title': f"High Breach Rate: {policy.name}",
                    'description': f"This policy has been breached {item['breach_count']} times recently. Consider adjusting the deadline or optimizing the resource allocation for {policy.module_scope}.",
                    'breach_count': item['breach_count'],
                    'impacted_module': policy.module_scope,
                    'suggested_fix': "Increase deadline_minutes or automate the underlying task."
                }
            )
            if created: insights_created += 1
            
        return insights_created
