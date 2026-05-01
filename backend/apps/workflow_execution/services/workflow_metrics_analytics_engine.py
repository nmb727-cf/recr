from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from django.db.models import Avg, Count
from django.utils import timezone

from apps.workflow_execution.models import (
    WorkflowActionExecutionLog,
    WorkflowActionMetric,
    WorkflowAutomationImpactMetric,
    WorkflowFailureLog,
    WorkflowFailureMetric,
    WorkflowInstance,
    WorkflowMetricSnapshot,
    WorkflowNotificationLog,
    WorkflowRecoveryCase,
    WorkflowSLAEvent,
    WorkflowStageExecution,
    WorkflowStageMetric,
    WorkflowWaitState,
)


class WorkflowMetricsAnalyticsEngine:
    @staticmethod
    def _normalize_date(metric_date: date | datetime | None) -> date:
        if metric_date is None:
            return timezone.localdate()
        if isinstance(metric_date, str):
            return date.fromisoformat(metric_date)
        if isinstance(metric_date, datetime):
            return metric_date.date()
        return metric_date

    @staticmethod
    def calculate_workflow_completion_time(*, workflow_id, metric_date: date | None = None) -> float:
        metric_date = WorkflowMetricsAnalyticsEngine._normalize_date(metric_date)
        instances = WorkflowInstance.objects.filter(
            workflow_id=workflow_id,
            status='completed',
            completed_at__date=metric_date,
        )
        durations: list[float] = []
        for instance in instances:
            if instance.completed_at and instance.started_at:
                durations.append((instance.completed_at - instance.started_at).total_seconds())
        if not durations:
            return 0.0
        return round(sum(durations) / len(durations), 2)

    @staticmethod
    def calculate_wait_time(*, workflow_id, metric_date: date | None = None, stage_id=None) -> float:
        metric_date = WorkflowMetricsAnalyticsEngine._normalize_date(metric_date)
        waits = WorkflowWaitState.objects.filter(
            workflow_instance__workflow_id=workflow_id,
            created_at__date=metric_date,
        )
        if stage_id is not None:
            waits = waits.filter(stage_execution__stage_id=stage_id)

        durations: list[float] = []
        for wait in waits:
            end_time = wait.resumed_at or wait.updated_at or wait.created_at
            if end_time and wait.created_at:
                durations.append((end_time - wait.created_at).total_seconds())
        if not durations:
            return 0.0
        return round(sum(durations) / len(durations), 2)

    @staticmethod
    def generate_workflow_metric_snapshot(*, workflow_id, snapshot_date: date | None = None) -> WorkflowMetricSnapshot:
        snapshot_date = WorkflowMetricsAnalyticsEngine._normalize_date(snapshot_date)
        instances = WorkflowInstance.objects.filter(workflow_id=workflow_id, started_at__date=snapshot_date)
        total_instances = instances.count()
        completed_instances = instances.filter(status='completed').count()
        failed_instances = instances.filter(status='failed').count()
        in_progress_instances = instances.filter(status__in=['pending', 'running', 'waiting', 'paused']).count()

        stage_counts = (
            WorkflowStageExecution.objects.filter(
                workflow_instance__workflow_id=workflow_id,
                workflow_instance__started_at__date=snapshot_date,
            )
            .values('workflow_instance_id')
            .annotate(c=Count('id'))
        )
        avg_stage_count = round(
            sum(row['c'] for row in stage_counts) / len(stage_counts),
            2,
        ) if stage_counts else 0.0

        retry_qs = WorkflowFailureLog.objects.filter(
            workflow_instance__workflow_id=workflow_id,
            workflow_instance__started_at__date=snapshot_date,
        )
        avg_retry_count = float(retry_qs.aggregate(v=Avg('retry_count')).get('v') or 0.0)

        wait_avg = WorkflowMetricsAnalyticsEngine.calculate_wait_time(
            workflow_id=workflow_id,
            metric_date=snapshot_date,
        )
        completion_avg = WorkflowMetricsAnalyticsEngine.calculate_workflow_completion_time(
            workflow_id=workflow_id,
            metric_date=snapshot_date,
        )

        tenant_id = instances.first().tenant_id if total_instances else None
        snapshot, _ = WorkflowMetricSnapshot.objects.update_or_create(
            workflow_id=workflow_id,
            snapshot_date=snapshot_date,
            defaults={
                'tenant_id': tenant_id,
                'total_instances': total_instances,
                'completed_instances': completed_instances,
                'failed_instances': failed_instances,
                'in_progress_instances': in_progress_instances,
                'average_completion_time_seconds': completion_avg,
                'average_wait_time_seconds': wait_avg,
                'average_stage_count': avg_stage_count,
                'average_retry_count': round(avg_retry_count, 2),
            },
        )
        return snapshot

    @staticmethod
    def generate_stage_metrics(*, workflow_id, metric_date: date | None = None) -> list[WorkflowStageMetric]:
        metric_date = WorkflowMetricsAnalyticsEngine._normalize_date(metric_date)
        stage_ids = list(
            WorkflowStageExecution.objects.filter(
                workflow_instance__workflow_id=workflow_id,
                started_at__date=metric_date,
            ).values_list('stage_id', flat=True).distinct()
        )

        metrics: list[WorkflowStageMetric] = []
        for stage_id in stage_ids:
            stage_execs = WorkflowStageExecution.objects.filter(
                workflow_instance__workflow_id=workflow_id,
                stage_id=stage_id,
                started_at__date=metric_date,
            )
            total_entries = stage_execs.count()
            completed_entries = stage_execs.filter(status='completed').count()
            failed_entries = stage_execs.filter(status='failed').count()

            durations: list[float] = []
            for stage_exec in stage_execs:
                end_time = stage_exec.completed_at or stage_exec.failed_at
                if stage_exec.started_at and end_time:
                    durations.append((end_time - stage_exec.started_at).total_seconds())
            avg_time = round(sum(durations) / len(durations), 2) if durations else 0.0

            avg_wait = WorkflowMetricsAnalyticsEngine.calculate_wait_time(
                workflow_id=workflow_id,
                metric_date=metric_date,
                stage_id=stage_id,
            )

            failures = WorkflowFailureLog.objects.filter(
                workflow_instance__workflow_id=workflow_id,
                stage_execution__stage_id=stage_id,
                created_at__date=metric_date,
            )
            avg_retry = float(failures.aggregate(v=Avg('retry_count')).get('v') or 0.0)

            sla_breach_count = WorkflowSLAEvent.objects.filter(
                workflow_instance__workflow_id=workflow_id,
                stage_execution__stage_id=stage_id,
                event_type='breach',
                created_at__date=metric_date,
            ).count()

            tenant_id = stage_execs.first().tenant_id if total_entries else None
            metric, _ = WorkflowStageMetric.objects.update_or_create(
                workflow_id=workflow_id,
                stage_id=stage_id,
                metric_date=metric_date,
                defaults={
                    'tenant_id': tenant_id,
                    'total_entries': total_entries,
                    'completed_entries': completed_entries,
                    'failed_entries': failed_entries,
                    'average_time_in_stage_seconds': avg_time,
                    'average_wait_time_seconds': avg_wait,
                    'average_retry_count': round(avg_retry, 2),
                    'sla_breach_count': sla_breach_count,
                },
            )
            metrics.append(metric)
        return metrics

    @staticmethod
    def generate_failure_metrics(*, workflow_id, metric_date: date | None = None) -> list[WorkflowFailureMetric]:
        metric_date = WorkflowMetricsAnalyticsEngine._normalize_date(metric_date)
        failures = WorkflowFailureLog.objects.filter(
            workflow_instance__workflow_id=workflow_id,
            created_at__date=metric_date,
        )

        grouped: dict[tuple[Any, str], list[WorkflowFailureLog]] = {}
        for failure in failures:
            stage_id = failure.stage_execution.stage_id if failure.stage_execution else None
            key = (stage_id, str(failure.error_type or 'unknown'))
            grouped.setdefault(key, []).append(failure)

        metrics: list[WorkflowFailureMetric] = []
        for (stage_id, failure_type), rows in grouped.items():
            stage_failures = len(rows)
            related_cases = WorkflowRecoveryCase.objects.filter(
                workflow_instance__workflow_id=workflow_id,
                stage_execution__stage_id=stage_id,
                failure_type=failure_type,
                created_at__date=metric_date,
            )
            recovered_count = related_cases.filter(status='recovered').count()
            permanent_failure_count = related_cases.filter(status='failed_permanently').count()

            recovery_durations: list[float] = []
            for rc in related_cases.filter(resolved_at__isnull=False):
                recovery_durations.append((rc.resolved_at - rc.created_at).total_seconds())
            avg_recovery = round(sum(recovery_durations) / len(recovery_durations), 2) if recovery_durations else 0.0

            tenant_id = rows[0].tenant_id if rows else None
            metric, _ = WorkflowFailureMetric.objects.update_or_create(
                workflow_id=workflow_id,
                stage_id=stage_id,
                metric_date=metric_date,
                failure_type=failure_type,
                defaults={
                    'tenant_id': tenant_id,
                    'failure_count': stage_failures,
                    'recovered_count': recovered_count,
                    'permanent_failure_count': permanent_failure_count,
                    'average_recovery_time_seconds': avg_recovery,
                },
            )
            metrics.append(metric)
        return metrics

    @staticmethod
    def generate_action_metrics(*, workflow_id, metric_date: date | None = None) -> list[WorkflowActionMetric]:
        metric_date = WorkflowMetricsAnalyticsEngine._normalize_date(metric_date)
        action_logs = WorkflowActionExecutionLog.objects.filter(
            workflow_instance__workflow_id=workflow_id,
            created_at__date=metric_date,
        )

        grouped: dict[tuple[Any, str], list[WorkflowActionExecutionLog]] = {}
        for row in action_logs:
            stage_id = row.stage_execution.stage_id if row.stage_execution else None
            key = (stage_id, row.action_type)
            grouped.setdefault(key, []).append(row)

        metrics: list[WorkflowActionMetric] = []
        for (stage_id, action_type), rows in grouped.items():
            execution_count = len(rows)
            success_count = len([r for r in rows if r.status == 'completed'])
            failure_count = len([r for r in rows if r.status == 'failed'])

            durations: list[float] = []
            for row in rows:
                if row.started_at and row.completed_at:
                    durations.append((row.completed_at - row.started_at).total_seconds())
            avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0

            metric, _ = WorkflowActionMetric.objects.update_or_create(
                workflow_id=workflow_id,
                stage_id=stage_id,
                action_type=action_type,
                metric_date=metric_date,
                defaults={
                    'tenant_id': rows[0].tenant_id if rows else None,
                    'execution_count': execution_count,
                    'success_count': success_count,
                    'failure_count': failure_count,
                    'average_duration_seconds': avg_duration,
                },
            )
            metrics.append(metric)
        return metrics

    @staticmethod
    def generate_automation_impact_metrics(*, workflow_id, metric_date: date | None = None) -> WorkflowAutomationImpactMetric:
        metric_date = WorkflowMetricsAnalyticsEngine._normalize_date(metric_date)

        action_logs = WorkflowActionExecutionLog.objects.filter(
            workflow_instance__workflow_id=workflow_id,
            created_at__date=metric_date,
            status='completed',
        )
        tasks_automated = action_logs.filter(action_type='create_task').count()
        approvals_automated = action_logs.filter(action_type='request_approval').count()

        notifications_sent = WorkflowNotificationLog.objects.filter(
            workflow_instance__workflow_id=workflow_id,
            created_at__date=metric_date,
            status='sent',
        ).count()

        auto_action_count = action_logs.exclude(action_type='send_notification').count()
        manual_steps_saved = auto_action_count + approvals_automated
        estimated_time_saved_minutes = round(float(manual_steps_saved) * 7.5, 2)
        estimated_cost_saved = round(estimated_time_saved_minutes * 0.8, 2)

        tenant_ref = (
            WorkflowInstance.objects.filter(workflow_id=workflow_id).order_by('created_at').values_list('tenant_id', flat=True).first()
        )
        metric, _ = WorkflowAutomationImpactMetric.objects.update_or_create(
            workflow_id=workflow_id,
            metric_date=metric_date,
            defaults={
                'tenant_id': tenant_ref,
                'tasks_automated_count': tasks_automated,
                'approvals_automated_count': approvals_automated,
                'notifications_sent_count': notifications_sent,
                'manual_steps_saved_count': manual_steps_saved,
                'estimated_time_saved_minutes': estimated_time_saved_minutes,
                'estimated_cost_saved': estimated_cost_saved,
                'metadata': {
                    'assumptions': {
                        'minutes_per_manual_step': 7.5,
                        'cost_per_minute': 0.8,
                    }
                },
            },
        )
        return metric

    @staticmethod
    def calculate_bottlenecks(*, workflow_id, metric_date: date | None = None, limit: int = 5) -> dict[str, list[dict[str, Any]]]:
        metric_date = WorkflowMetricsAnalyticsEngine._normalize_date(metric_date)
        stage_metrics = WorkflowStageMetric.objects.filter(workflow_id=workflow_id, metric_date=metric_date)
        return {
            'slowest_stages': [
                {
                    'stage_id': str(row.stage_id),
                    'average_time_in_stage_seconds': row.average_time_in_stage_seconds,
                }
                for row in stage_metrics.order_by('-average_time_in_stage_seconds')[:limit]
            ],
            'longest_wait_stages': [
                {
                    'stage_id': str(row.stage_id),
                    'average_wait_time_seconds': row.average_wait_time_seconds,
                }
                for row in stage_metrics.order_by('-average_wait_time_seconds')[:limit]
            ],
            'most_failed_stages': [
                {
                    'stage_id': str(row.stage_id),
                    'failed_entries': row.failed_entries,
                }
                for row in stage_metrics.order_by('-failed_entries')[:limit]
            ],
            'stages_with_repeated_retries': [
                {
                    'stage_id': str(row.stage_id),
                    'average_retry_count': row.average_retry_count,
                }
                for row in stage_metrics.order_by('-average_retry_count')[:limit]
            ],
            'stages_with_most_sla_breaches': [
                {
                    'stage_id': str(row.stage_id),
                    'sla_breach_count': row.sla_breach_count,
                }
                for row in stage_metrics.order_by('-sla_breach_count')[:limit]
            ],
        }

    @staticmethod
    def summarize_workflow_health(*, workflow_id, metric_date: date | None = None) -> dict[str, Any]:
        metric_date = WorkflowMetricsAnalyticsEngine._normalize_date(metric_date)
        snapshot = WorkflowMetricsAnalyticsEngine.generate_workflow_metric_snapshot(
            workflow_id=workflow_id,
            snapshot_date=metric_date,
        )
        WorkflowMetricsAnalyticsEngine.generate_stage_metrics(workflow_id=workflow_id, metric_date=metric_date)
        WorkflowMetricsAnalyticsEngine.generate_failure_metrics(workflow_id=workflow_id, metric_date=metric_date)
        WorkflowMetricsAnalyticsEngine.generate_action_metrics(workflow_id=workflow_id, metric_date=metric_date)
        impact = WorkflowMetricsAnalyticsEngine.generate_automation_impact_metrics(
            workflow_id=workflow_id,
            metric_date=metric_date,
        )
        bottlenecks = WorkflowMetricsAnalyticsEngine.calculate_bottlenecks(
            workflow_id=workflow_id,
            metric_date=metric_date,
        )

        completion_rate = round(
            (snapshot.completed_instances / snapshot.total_instances) * 100,
            2,
        ) if snapshot.total_instances else 0.0
        failure_rate = round(
            (snapshot.failed_instances / snapshot.total_instances) * 100,
            2,
        ) if snapshot.total_instances else 0.0

        return {
            'workflow_id': str(workflow_id),
            'snapshot_date': snapshot.snapshot_date.isoformat(),
            'total_runs': snapshot.total_instances,
            'success_rate': completion_rate,
            'failure_rate': failure_rate,
            'average_completion_time_seconds': snapshot.average_completion_time_seconds,
            'average_wait_time_seconds': snapshot.average_wait_time_seconds,
            'average_retry_count': snapshot.average_retry_count,
            'time_saved_minutes': impact.estimated_time_saved_minutes,
            'estimated_cost_saved': impact.estimated_cost_saved,
            'bottlenecks': bottlenecks,
        }

    @staticmethod
    def build_workflow_trend_data(*, workflow_id, days: int = 30) -> dict[str, Any]:
        days = max(1, min(days, 365))
        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=days - 1)

        snapshots = WorkflowMetricSnapshot.objects.filter(
            workflow_id=workflow_id,
            snapshot_date__range=(start_date, end_date),
        ).order_by('snapshot_date')
        impacts = WorkflowAutomationImpactMetric.objects.filter(
            workflow_id=workflow_id,
            metric_date__range=(start_date, end_date),
        ).order_by('metric_date')
        failures = WorkflowFailureMetric.objects.filter(
            workflow_id=workflow_id,
            metric_date__range=(start_date, end_date),
        ).order_by('metric_date')

        failure_by_day: dict[date, int] = {}
        for row in failures:
            failure_by_day[row.metric_date] = failure_by_day.get(row.metric_date, 0) + int(row.failure_count)

        impact_by_day = {row.metric_date: row for row in impacts}

        series: list[dict[str, Any]] = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            snap = next((s for s in snapshots if s.snapshot_date == day), None)
            imp = impact_by_day.get(day)
            series.append(
                {
                    'date': day.isoformat(),
                    'total_runs': int(snap.total_instances if snap else 0),
                    'success_rate': round(
                        ((snap.completed_instances / snap.total_instances) * 100) if (snap and snap.total_instances) else 0.0,
                        2,
                    ),
                    'average_completion_time_seconds': float(snap.average_completion_time_seconds if snap else 0.0),
                    'average_wait_time_seconds': float(snap.average_wait_time_seconds if snap else 0.0),
                    'failure_count': int(failure_by_day.get(day, 0)),
                    'time_saved_minutes': float(imp.estimated_time_saved_minutes if imp else 0.0),
                    'estimated_cost_saved': float(imp.estimated_cost_saved if imp else 0.0),
                }
            )

        return {
            'workflow_id': str(workflow_id),
            'range': {'from': start_date.isoformat(), 'to': end_date.isoformat(), 'days': days},
            'series': series,
        }

    @staticmethod
    def run_analytics_rollup(*, workflow_id, metric_date: date | None = None) -> dict[str, Any]:
        metric_date = WorkflowMetricsAnalyticsEngine._normalize_date(metric_date)
        snapshot = WorkflowMetricsAnalyticsEngine.generate_workflow_metric_snapshot(
            workflow_id=workflow_id,
            snapshot_date=metric_date,
        )
        stage_metrics = WorkflowMetricsAnalyticsEngine.generate_stage_metrics(workflow_id=workflow_id, metric_date=metric_date)
        failure_metrics = WorkflowMetricsAnalyticsEngine.generate_failure_metrics(workflow_id=workflow_id, metric_date=metric_date)
        action_metrics = WorkflowMetricsAnalyticsEngine.generate_action_metrics(workflow_id=workflow_id, metric_date=metric_date)
        impact = WorkflowMetricsAnalyticsEngine.generate_automation_impact_metrics(workflow_id=workflow_id, metric_date=metric_date)
        return {
            'workflow_id': str(workflow_id),
            'metric_date': metric_date.isoformat(),
            'snapshot_id': str(snapshot.id),
            'stage_metric_count': len(stage_metrics),
            'failure_metric_count': len(failure_metrics),
            'action_metric_count': len(action_metrics),
            'impact_metric_id': str(impact.id),
        }


# Function-style exports required by prompt contract.
generate_workflow_metric_snapshot = WorkflowMetricsAnalyticsEngine.generate_workflow_metric_snapshot
generate_stage_metrics = WorkflowMetricsAnalyticsEngine.generate_stage_metrics
generate_failure_metrics = WorkflowMetricsAnalyticsEngine.generate_failure_metrics
generate_action_metrics = WorkflowMetricsAnalyticsEngine.generate_action_metrics
generate_automation_impact_metrics = WorkflowMetricsAnalyticsEngine.generate_automation_impact_metrics
calculate_workflow_completion_time = WorkflowMetricsAnalyticsEngine.calculate_workflow_completion_time
calculate_wait_time = WorkflowMetricsAnalyticsEngine.calculate_wait_time
calculate_bottlenecks = WorkflowMetricsAnalyticsEngine.calculate_bottlenecks
summarize_workflow_health = WorkflowMetricsAnalyticsEngine.summarize_workflow_health
build_workflow_trend_data = WorkflowMetricsAnalyticsEngine.build_workflow_trend_data
