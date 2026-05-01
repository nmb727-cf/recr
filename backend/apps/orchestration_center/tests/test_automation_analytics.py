from django.test import TestCase
from django.utils import timezone
from apps.orchestration_center.models.workflow import Workflow, WorkflowExecution, WorkflowExecutionLog
from apps.orchestration_center.models.analytics import (
    WorkflowAnalyticsSnapshot,
    WorkflowTriggerMetric,
    WorkflowFailureInsight,
    WorkflowImpactMetric
)
from apps.orchestration_center.services.automation_analytics_engine import AutomationAnalyticsEngine
import uuid

class AutomationAnalyticsTest(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name="Test Workflow",
            trigger_event="candidate_applied",
            is_active=True
        )

    def test_execution_metrics_snapshot(self):
        # Test 1: Workflow executed 10 times, 8 success, 2 fail
        for i in range(8):
            WorkflowExecution.objects.create(
                tenant_id=self.tenant_id,
                workflow=self.workflow,
                status='completed',
                started_at=timezone.now() - timezone.timedelta(minutes=5),
                completed_at=timezone.now()
            )
        for i in range(2):
            WorkflowExecution.objects.create(
                tenant_id=self.tenant_id,
                workflow=self.workflow,
                status='failed'
            )
            
        snapshot = AutomationAnalyticsEngine.generate_workflow_snapshot(self.tenant_id, self.workflow.id)
        
        self.assertEqual(snapshot.execution_count, 10)
        self.assertEqual(snapshot.success_count, 8)
        self.assertEqual(snapshot.failure_count, 2)
        self.assertEqual(snapshot.completion_rate, 80.0)
        self.assertEqual(snapshot.failure_rate, 20.0)

    def test_trigger_metrics(self):
        # Test 2: Trigger candidate_applied fires 15 times
        for i in range(15):
            AutomationAnalyticsEngine.track_trigger_metrics(self.tenant_id, self.workflow.id, "candidate_applied")
            
        metric = WorkflowTriggerMetric.objects.get(workflow=self.workflow, trigger_event="candidate_applied")
        self.assertEqual(metric.trigger_count, 15)

    def test_failure_pattern_detection(self):
        # Test 3: Workflow with repeated failure
        execution = WorkflowExecution.objects.create(tenant_id=self.tenant_id, workflow=self.workflow, status='failed')
        
        for i in range(3):
            WorkflowExecutionLog.objects.create(
                execution=execution,
                status='failed',
                message="SMTP Error: Connection timeout"
            )
            
        AutomationAnalyticsEngine.detect_failure_patterns(self.tenant_id, self.workflow.id)
        
        insight = WorkflowFailureInsight.objects.filter(workflow=self.workflow).first()
        self.assertIsNotNone(insight)
        self.assertTrue(insight.occurrence_count >= 3)
        self.assertIn("SMTP Error", insight.description)

    def test_impact_calculation(self):
        # Test 4: Impact metrics calculated
        WorkflowExecution.objects.create(tenant_id=self.tenant_id, workflow=self.workflow, status='completed')
        
        # Simulate a stage movement log
        exec_done = WorkflowExecution.objects.create(tenant_id=self.tenant_id, workflow=self.workflow, status='completed')
        WorkflowExecutionLog.objects.create(execution=exec_done, message="Automated moved stage to Interview")
        
        AutomationAnalyticsEngine.calculate_impact_metrics(self.tenant_id, self.workflow.id)
        
        hours = WorkflowImpactMetric.objects.get(workflow=self.workflow, impact_type='hours_saved')
        stages = WorkflowImpactMetric.objects.get(workflow=self.workflow, impact_type='stage_movements_automated')
        
        self.assertTrue(hours.metric_value > 0)
        self.assertEqual(stages.metric_value, 1)
