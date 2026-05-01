import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.orchestration_center.models.workflow import Workflow, WorkflowNode
from apps.workflow_execution.api.views import WorkflowAnalyticsTrendsView
from apps.workflow_execution.models import (
    WorkflowActionExecutionLog,
    WorkflowFailureLog,
    WorkflowNotificationLog,
    WorkflowRecoveryCase,
    WorkflowStageExecution,
    WorkflowWaitState,
)
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_metrics_analytics_engine import WorkflowMetricsAnalyticsEngine


class TestWorkflowMetricsAnalyticsEngine(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Metrics Workflow',
            trigger_event='job_created',
            status='active',
            is_active=True,
        )
        self.stage_a = WorkflowNode.objects.create(workflow=self.workflow, node_type='action', config={'label': 'Review'})
        self.stage_b = WorkflowNode.objects.create(workflow=self.workflow, node_type='action', config={'label': 'Interview'})

    def _instance(self, status='running'):
        instance = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='candidate',
            entity_id=uuid.uuid4(),
            status=status,
        )
        return instance

    def test_1_completed_instances_snapshot_generated(self):
        now = timezone.now()
        for _ in range(2):
            instance = self._instance(status='completed')
            instance.started_at = now - timedelta(hours=3)
            instance.completed_at = now
            instance.save(update_fields=['started_at', 'completed_at', 'updated_at'])

        failed = self._instance(status='failed')
        failed.started_at = now - timedelta(hours=2)
        failed.failed_at = now
        failed.save(update_fields=['started_at', 'failed_at', 'updated_at'])

        self._instance(status='running')

        snapshot = WorkflowMetricsAnalyticsEngine.generate_workflow_metric_snapshot(workflow_id=self.workflow.id)
        self.assertEqual(snapshot.total_instances, 4)
        self.assertEqual(snapshot.completed_instances, 2)
        self.assertEqual(snapshot.failed_instances, 1)

    def test_2_long_wait_reflected_in_stage_metrics_and_bottleneck(self):
        instance = self._instance(status='running')
        stage_exec = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_id=self.stage_a.id,
            stage_name='Review',
            status='completed',
            started_at=timezone.now() - timedelta(hours=5),
            completed_at=timezone.now(),
        )

        wait = WorkflowWaitState.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_exec,
            wait_type='manual',
            wait_reason='Waiting for recruiter',
            status='resumed',
            resumed_at=timezone.now(),
        )
        wait.created_at = timezone.now() - timedelta(hours=4)
        wait.save(update_fields=['created_at', 'updated_at'])

        metrics = WorkflowMetricsAnalyticsEngine.generate_stage_metrics(workflow_id=self.workflow.id)
        self.assertTrue(any(m.average_wait_time_seconds > 0 for m in metrics))

        bottlenecks = WorkflowMetricsAnalyticsEngine.calculate_bottlenecks(workflow_id=self.workflow.id)
        self.assertTrue(len(bottlenecks['longest_wait_stages']) >= 1)

    def test_3_recovered_retry_updates_failure_metrics(self):
        instance = self._instance(status='running')
        stage_exec = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_id=self.stage_a.id,
            stage_name='Review',
            status='failed',
            started_at=timezone.now() - timedelta(hours=2),
            failed_at=timezone.now() - timedelta(hours=1),
        )
        WorkflowFailureLog.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_exec,
            error_message='Timeout from downstream',
            error_type='timeout',
            retry_count=1,
            status='retrying',
        )

        recovered = WorkflowRecoveryCase.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_exec,
            recovery_type='stage_failure',
            failure_type='timeout',
            error_message='Recovered timeout',
            error_code='timeout',
            status='recovered',
            retry_strategy='immediate',
            retry_limit=2,
            retry_count=1,
            resolved_at=timezone.now(),
        )
        recovered.created_at = timezone.now() - timedelta(minutes=30)
        recovered.save(update_fields=['created_at', 'resolved_at', 'updated_at'])

        metrics = WorkflowMetricsAnalyticsEngine.generate_failure_metrics(workflow_id=self.workflow.id)
        timeout_metric = next(m for m in metrics if m.failure_type == 'timeout')
        self.assertGreaterEqual(timeout_metric.failure_count, 1)
        self.assertGreaterEqual(timeout_metric.recovered_count, 1)

    def test_4_action_logs_aggregate_action_metrics(self):
        instance = self._instance(status='running')
        stage_exec = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_id=self.stage_b.id,
            stage_name='Interview',
            status='running',
            started_at=timezone.now() - timedelta(hours=1),
        )

        WorkflowActionExecutionLog.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_exec,
            action_type='create_interview',
            status='completed',
            started_at=timezone.now() - timedelta(minutes=10),
            completed_at=timezone.now() - timedelta(minutes=8),
        )
        WorkflowActionExecutionLog.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_exec,
            action_type='create_interview',
            status='failed',
            started_at=timezone.now() - timedelta(minutes=7),
            completed_at=timezone.now() - timedelta(minutes=6),
            error_message='provider unavailable',
        )

        metrics = WorkflowMetricsAnalyticsEngine.generate_action_metrics(workflow_id=self.workflow.id)
        interview_metric = next(m for m in metrics if m.action_type == 'create_interview')
        self.assertEqual(interview_metric.execution_count, 2)
        self.assertEqual(interview_metric.success_count, 1)
        self.assertEqual(interview_metric.failure_count, 1)

    def test_5_automation_impact_generated(self):
        instance = self._instance(status='running')
        stage_exec = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_id=self.stage_b.id,
            stage_name='Interview',
            status='running',
            started_at=timezone.now() - timedelta(minutes=30),
        )

        WorkflowActionExecutionLog.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_exec,
            action_type='create_task',
            status='completed',
            started_at=timezone.now() - timedelta(minutes=20),
            completed_at=timezone.now() - timedelta(minutes=19),
        )
        WorkflowActionExecutionLog.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_exec,
            action_type='request_approval',
            status='completed',
            started_at=timezone.now() - timedelta(minutes=18),
            completed_at=timezone.now() - timedelta(minutes=17),
        )
        WorkflowNotificationLog.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=instance,
            stage_execution=stage_exec,
            recipient_type='recruiter',
            channel='email',
            template_key='workflow_stage_started',
            message_preview='Interview stage started',
            status='sent',
            sent_at=timezone.now() - timedelta(minutes=16),
        )

        impact = WorkflowMetricsAnalyticsEngine.generate_automation_impact_metrics(workflow_id=self.workflow.id)
        self.assertGreaterEqual(impact.tasks_automated_count, 1)
        self.assertGreaterEqual(impact.approvals_automated_count, 1)
        self.assertGreaterEqual(impact.notifications_sent_count, 1)
        self.assertGreater(impact.estimated_time_saved_minutes, 0)

    def test_6_trend_endpoint_returns_time_series(self):
        WorkflowMetricsAnalyticsEngine.run_analytics_rollup(workflow_id=self.workflow.id)
        factory = APIRequestFactory()
        request = factory.get('/api/v1/workflow-analytics/workflows/test/trends/', {'days': 7})
        user = get_user_model().objects.create_user(email='metrics-test@example.com', password='pass1234')
        from rest_framework.test import force_authenticate
        force_authenticate(request, user=user)
        view = WorkflowAnalyticsTrendsView.as_view()
        res = view(request, workflow_id=self.workflow.id)
        self.assertEqual(res.status_code, 200)
        payload = res.data
        self.assertEqual(payload['range']['days'], 7)
        self.assertEqual(len(payload['series']), 7)
