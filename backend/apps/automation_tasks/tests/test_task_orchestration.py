"""
Automation Task Orchestration — test suite

Covers all 4 spec acceptance tests plus additional API/engine tests.
"""
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.automation_tasks.models import (
    TaskPriority,
    TaskStatus,
    WorkflowTaskDependency,
    WorkflowTaskEscalation,
    WorkflowTaskExecution,
    WorkflowTaskRule,
)
from apps.automation_tasks.services.workflow_task_orchestrator import WorkflowTaskOrchestrator
from apps.automation_tasks.views import (
    TaskAnalyticsView,
    TaskCompleteView,
    TaskExecutionListView,
    TaskRuleListView,
    TaskTestView,
)

TENANT_ID   = uuid.UUID('00000000-0000-0000-0000-000000000001')
WORKFLOW_ID = uuid.UUID('00000000-0000-0000-0000-000000000010')


def _user(role: str) -> CustomUser:
    email = f'{role}-tasks@example.com'
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return CustomUser.objects.create_user(
            email=email, password='testpass123', role=role, tenant_id=TENANT_ID,
        )


def _make_rule(**kwargs) -> WorkflowTaskRule:
    defaults = dict(
        tenant_id=TENANT_ID,
        workflow_id=WORKFLOW_ID,
        task_title_template='Review {{candidate_name}} for {{job_title}}',
        task_description_template='Candidate applied via {{source}}. Review within {{due_time}}.',
        assignee_type='assigned_recruiter',
        priority=TaskPriority.HIGH,
        due_in_minutes=1440,
        escalate_after_minutes=2880,
        is_active=True,
    )
    defaults.update(kwargs)
    return WorkflowTaskRule.objects.create(**defaults)


def _candidate_context(recruiter_id=None):
    return {
        'candidate_name':     'Alice Johnson',
        'job_title':          'Backend Engineer',
        'source':             'LinkedIn',
        'due_time':           '24 hours',
        'recruiter_id':       str(recruiter_id or uuid.uuid4()),
        'hiring_manager_id':  str(uuid.uuid4()),
        'recruiter_manager_id': str(uuid.uuid4()),
    }


# ─── Test 1: Candidate applied → task created ─────────────────────────────────

class TaskCreationTests(TestCase):

    def test_candidate_applied_creates_task(self):
        """Workflow triggered on candidate.applied → task created with correct fields."""
        rule = _make_rule()
        ctx  = _candidate_context()

        task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID,
            workflow_id=WORKFLOW_ID,
            rule=rule,
            context=ctx,
        )

        self.assertIsNotNone(task.id)
        self.assertEqual(task.tenant_id, TENANT_ID)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertIn('Alice Johnson', task.task_title)
        self.assertIn('Backend Engineer', task.task_title)
        self.assertIsNotNone(task.due_at)

    def test_template_placeholders_rendered(self):
        rule = _make_rule()
        ctx  = _candidate_context()
        task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
        )
        self.assertIn('Alice Johnson', task.task_title)
        self.assertIn('LinkedIn', task.task_description)

    def test_assignee_resolved_from_context(self):
        recruiter_id = uuid.uuid4()
        rule = _make_rule(assignee_type='assigned_recruiter')
        ctx  = _candidate_context(recruiter_id=recruiter_id)
        task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
        )
        self.assertEqual(str(task.assignee_user_id), str(recruiter_id))


# ─── Test 2: Task overdue → escalation triggered ─────────────────────────────

class TaskEscalationTests(TestCase):

    def test_overdue_task_triggers_escalation(self):
        """Task overdue → escalation created and task status = ESCALATED."""
        rule = _make_rule(escalate_after_minutes=1)
        ctx  = _candidate_context()
        task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
        )
        # Make task overdue
        task.due_at = timezone.now() - timedelta(hours=2)
        task.save()

        with patch.object(WorkflowTaskOrchestrator, '_send_escalation_notification'):
            escalation = WorkflowTaskOrchestrator.escalate_task(
                task, reason='SLA exceeded'
            )

        self.assertIsNotNone(escalation.id)
        self.assertEqual(escalation.escalation_level, 1)
        self.assertIn(escalation.escalated_to_role, ['recruiter_manager', 'hr_manager', 'tenant_admin'])

        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.ESCALATED)
        self.assertTrue(task.escalated)

    def test_escalation_level_increments(self):
        """Second escalation is L2."""
        rule = _make_rule()
        ctx  = _candidate_context()
        task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
        )

        with patch.object(WorkflowTaskOrchestrator, '_send_escalation_notification'):
            esc1 = WorkflowTaskOrchestrator.escalate_task(task, reason='First escalation')
            # Reset status to allow second escalation
            task.status = TaskStatus.OVERDUE
            task.save()
            esc2 = WorkflowTaskOrchestrator.escalate_task(task, reason='Second escalation')

        self.assertEqual(esc1.escalation_level, 1)
        self.assertEqual(esc2.escalation_level, 2)

    def test_track_status_marks_overdue(self):
        """track_task_status marks overdue tasks and escalates when threshold exceeded."""
        rule = _make_rule(escalate_after_minutes=1)
        ctx  = _candidate_context()
        task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
        )
        # Backdate due_at and created_at to simulate elapsed SLA
        WorkflowTaskExecution.objects.filter(id=task.id).update(
            due_at=timezone.now() - timedelta(hours=3),
            created_at=timezone.now() - timedelta(hours=3),
        )

        with patch.object(WorkflowTaskOrchestrator, '_send_escalation_notification'):
            result = WorkflowTaskOrchestrator.track_task_status(TENANT_ID)

        self.assertIn(str(task.id), result['overdue'])


# ─── Test 3: Task completed → next workflow step ─────────────────────────────

class TaskCompletionTests(TestCase):

    def test_complete_task_trigger(self):
        """Task completed → result shows completed status."""
        rule = _make_rule()
        ctx  = _candidate_context()
        task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
        )
        result = WorkflowTaskOrchestrator.complete_task_trigger(task)

        self.assertEqual(result['status'], TaskStatus.COMPLETED)
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)

    def test_complete_via_api(self):
        factory = APIRequestFactory()
        admin   = _user('tenant_admin')
        rule    = _make_rule()
        task    = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=_candidate_context(),
        )
        request = factory.post(f'/api/v1/workflow-tasks/executions/{task.id}/complete/')
        force_authenticate(request, user=admin)
        response = TaskCompleteView.as_view()(request, pk=task.id)
        self.assertEqual(response.status_code, 200)

        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.COMPLETED)


# ─── Test 4: Dependent task → created after completion ───────────────────────

class TaskDependencyTests(TestCase):

    def test_dependent_task_unlocked_on_completion(self):
        """
        Screening Task → Interview Scheduling Task.
        Interview Scheduling only starts when Screening is completed.
        """
        rule = _make_rule()
        ctx  = _candidate_context()

        screening_task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
        )
        interview_task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
            depends_on_task_id=screening_task.id,
        )

        # Dependency exists
        dep = WorkflowTaskDependency.objects.filter(
            task_execution=interview_task,
            depends_on_task=screening_task,
        ).first()
        self.assertIsNotNone(dep)

        # Before completion: interview task not yet active
        all_done = WorkflowTaskOrchestrator.resolve_dependencies(interview_task)
        self.assertFalse(all_done)
        interview_task.refresh_from_db()
        self.assertEqual(interview_task.status, TaskStatus.PENDING)

        # Complete the screening task
        result = WorkflowTaskOrchestrator.complete_task_trigger(screening_task)

        # Interview task should now be unlocked (in_progress)
        interview_task.refresh_from_db()
        self.assertEqual(interview_task.status, TaskStatus.IN_PROGRESS)
        self.assertIn(str(interview_task.id), result['unlocked_tasks'])

    def test_three_stage_chain(self):
        """Screening → Interview → Offer: each unlocked sequentially."""
        rule = _make_rule()
        ctx  = _candidate_context()

        t1 = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
        )
        t2 = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
            depends_on_task_id=t1.id,
        )
        t3 = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
            depends_on_task_id=t2.id,
        )

        WorkflowTaskOrchestrator.complete_task_trigger(t1)
        t2.refresh_from_db()
        self.assertEqual(t2.status, TaskStatus.IN_PROGRESS)
        # t3 still locked
        t3.refresh_from_db()
        self.assertEqual(t3.status, TaskStatus.PENDING)

        WorkflowTaskOrchestrator.complete_task_trigger(t2)
        t3.refresh_from_db()
        self.assertEqual(t3.status, TaskStatus.IN_PROGRESS)


# ─── API tests ────────────────────────────────────────────────────────────────

class TaskAPITests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin   = _user('tenant_admin')
        self.manager = _user('hr_manager')
        self.recruiter = _user('recruiter')

    def test_admin_can_create_rule(self):
        request = self.factory.post(
            '/api/v1/workflow-tasks/rules/',
            {
                'workflow_id': str(WORKFLOW_ID),
                'task_title_template': 'Review {{candidate_name}}',
                'assignee_type': 'assigned_recruiter',
                'priority': 'high',
                'due_in_minutes': 1440,
                'escalate_after_minutes': 2880,
                'is_active': True,
            },
            format='json',
        )
        force_authenticate(request, user=self.admin)
        response = TaskRuleListView.as_view()(request)
        self.assertEqual(response.status_code, 201)

    def test_recruiter_can_view_executions(self):
        request = self.factory.get('/api/v1/workflow-tasks/executions/')
        force_authenticate(request, user=self.recruiter)
        response = TaskExecutionListView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_manager_can_view_analytics(self):
        request = self.factory.get('/api/v1/workflow-tasks/analytics/')
        force_authenticate(request, user=self.manager)
        response = TaskAnalyticsView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        data = response.data.get('data', {}).get('analytics', {})
        self.assertIn('total', data)
        self.assertIn('completion_rate', data)

    def test_analytics_counts_correct(self):
        rule = _make_rule()
        ctx  = _candidate_context()
        t1   = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=TENANT_ID, workflow_id=WORKFLOW_ID, rule=rule, context=ctx,
        )
        WorkflowTaskOrchestrator.complete_task_trigger(t1)

        request = self.factory.get('/api/v1/workflow-tasks/analytics/')
        force_authenticate(request, user=self.manager)
        response = TaskAnalyticsView.as_view()(request)
        analytics = response.data['data']['analytics']
        self.assertGreaterEqual(analytics['completed'], 1)
