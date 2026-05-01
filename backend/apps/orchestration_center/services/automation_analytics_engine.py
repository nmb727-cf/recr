from django.db import models
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from datetime import timedelta
from apps.orchestration_center.models.workflow import Workflow, WorkflowExecution, WorkflowExecutionLog
from apps.orchestration_center.models.analytics import (
    WorkflowAnalyticsSnapshot,
    WorkflowActionMetric,
    WorkflowTriggerMetric,
    WorkflowImpactMetric,
    WorkflowFailureInsight,
)

class AutomationAnalyticsEngine:
    @staticmethod
    def generate_workflow_snapshot(tenant_id, workflow_id, date=None):
        if date is None:
            date = timezone.now().date()
        
        since = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.min.time()))
        until = since + timedelta(days=1)
        
        executions = WorkflowExecution.objects.filter(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            started_at__gte=since,
            started_at__lt=until
        )
        
        count = executions.count()
        if count == 0:
            return None
            
        success = executions.filter(status='completed').count()
        failure = executions.filter(status='failed').count()
        paused = executions.filter(status='paused').count()
        
        # Duration calc
        durations = []
        for e in executions.filter(status='completed', started_at__isnull=False, completed_at__isnull=False):
            durations.append((e.completed_at - e.started_at).total_seconds() * 1000)
            
        avg_time = sum(durations) / len(durations) if durations else 0
        
        # Steps calc
        steps = WorkflowExecutionLog.objects.filter(execution__in=executions).values('execution_id').annotate(count=Count('id'))
        avg_steps = sum(s['count'] for s in steps) / count if count > 0 else 0
        
        snapshot, _ = WorkflowAnalyticsSnapshot.objects.update_or_create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            snapshot_date=date,
            defaults={
                'execution_count': count,
                'success_count': success,
                'failure_count': failure,
                'paused_count': paused,
                'avg_execution_time_ms': avg_time,
                'avg_steps_per_execution': avg_steps,
                'completion_rate': (success / count * 100) if count > 0 else 0,
                'failure_rate': (failure / count * 100) if count > 0 else 0,
            }
        )
        return snapshot

    @staticmethod
    def track_trigger_metrics(tenant_id, workflow_id, trigger_event):
        metric, _ = WorkflowTriggerMetric.objects.get_or_create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            trigger_event=trigger_event
        )
        metric.trigger_count = models.F('trigger_count') + 1
        metric.save()

    @staticmethod
    def track_action_metrics(tenant_id, workflow_id, action_type, success=True, duration_ms=0):
        metric, _ = WorkflowActionMetric.objects.get_or_create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            action_type=action_type
        )
        metric.action_count = models.F('action_count') + 1
        if success:
            metric.success_count = models.F('success_count') + 1
        else:
            metric.failure_count = models.F('failure_count') + 1
            
        # Approximation of running average
        if duration_ms > 0:
            metric.avg_action_time_ms = (models.F('avg_action_time_ms') * models.F('action_count') + duration_ms) / (models.F('action_count') + 1)
            
        metric.save()

    @staticmethod
    def calculate_impact_metrics(tenant_id, workflow_id):
        workflow = Workflow.objects.get(id=workflow_id)
        executions = WorkflowExecution.objects.filter(workflow_id=workflow_id, status='completed')
        count = executions.count()
        
        # 1. Hours saved: Assume 10 mins per manual action for simplicity
        # In a real system, this would be config-based
        hours_saved = (count * 10) / 60.0
        WorkflowImpactMetric.objects.update_or_create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            impact_type='hours_saved',
            defaults={'metric_value': hours_saved, 'metric_unit': 'hours'}
        )
        
        # 2. Stage movements
        movements = WorkflowExecutionLog.objects.filter(
            execution__workflow_id=workflow_id, 
            message__icontains='moved stage'
        ).count()
        if movements > 0:
            WorkflowImpactMetric.objects.update_or_create(
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                impact_type='stage_movements_automated',
                defaults={'metric_value': movements, 'metric_unit': 'count'}
            )

        # 3. Reminders
        reminders = WorkflowExecutionLog.objects.filter(
            execution__workflow_id=workflow_id,
            message__icontains='reminder'
        ).count()
        if reminders > 0:
            WorkflowImpactMetric.objects.update_or_create(
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                impact_type='reminders_sent',
                defaults={'metric_value': reminders, 'metric_unit': 'count'}
            )

    @staticmethod
    def detect_failure_patterns(tenant_id, workflow_id):
        recent_failures = WorkflowExecutionLog.objects.filter(
            execution__workflow_id=workflow_id,
            status='failed'
        ).order_by('-executed_at')[:100]
        
        patterns = {}
        for fail in recent_failures:
            node_type = fail.node.node_type if fail.node else 'unknown'
            msg = fail.message or 'No message'
            key = f"{node_type}:{msg[:50]}"
            if key not in patterns:
                patterns[key] = {'count': 0, 'last_seen': fail.executed_at, 'type': node_type, 'msg': msg}
            patterns[key]['count'] += 1
            
        for key, data in patterns.items():
            if data['count'] >= 3: # Pattern threshold
                WorkflowFailureInsight.objects.update_or_create(
                    tenant_id=tenant_id,
                    workflow_id=workflow_id,
                    failure_type=data['type'],
                    title=f"Frequent failure in {data['type']} node",
                    defaults={
                        'description': data['msg'],
                        'occurrence_count': data['count'],
                        'last_seen_at': data['last_seen'],
                        'status': 'new'
                    }
                )

    @staticmethod
    def generate_analytics_insights(tenant_id):
        insights = []
        
        # 1. Reduction in time-to-action (stubbed logic for demo)
        # 2. Never triggered workflows
        inactive_workflows = Workflow.objects.filter(tenant_id=tenant_id, is_active=True).annotate(
            run_count=Count('executions')
        ).filter(run_count=0)
        
        for wf in inactive_workflows:
            insights.append(f"Workflow '{wf.name}' is active but has never been triggered.")
            
        # 3. High impact workflows
        impactful = WorkflowImpactMetric.objects.filter(tenant_id=tenant_id, impact_type='hours_saved', metric_value__gt=10)
        for imp in impactful:
            insights.append(f"Workflow '{imp.workflow.name}' has saved over {imp.metric_value} manual hours.")
            
        return insights
