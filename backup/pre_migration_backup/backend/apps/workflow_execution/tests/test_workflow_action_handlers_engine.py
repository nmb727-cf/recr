import uuid

from django.test import TestCase

from apps.orchestration_center.models.workflow import Workflow, WorkflowNode
from apps.workflow_execution.models import (
    WorkflowActionDefinition,
    WorkflowActionExecutionLog,
    WorkflowActorAssignment,
    WorkflowInstance,
    WorkflowScheduledTask,
    WorkflowStageExecution,
)
from apps.workflow_execution.services.workflow_action_handlers_engine import WorkflowActionHandlersEngine


def make_workflow(tenant_id):
    workflow = Workflow.objects.create(
        tenant_id=tenant_id,
        name='Action Handler WF',
        trigger_event='job_created',
        status='active',
        is_active=True,
    )
    stage = WorkflowNode.objects.create(workflow=workflow, node_type='action')
    return workflow, stage


class TestWorkflowActionHandlersEngine(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.workflow, self.stage = make_workflow(self.tenant_id)
        self.instance = WorkflowInstance.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='candidate',
            entity_id=uuid.uuid4(),
            current_stage_id=self.stage.id,
            status='running',
            context_data={},
        )
        self.stage_execution = WorkflowStageExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow_instance=self.instance,
            stage_id=self.stage.id,
            stage_name='action',
            status='running',
        )

    def test_1_assign_actor_then_create_task_execution_order(self):
        WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Assign Recruiter',
            action_type='assign_actor',
            action_config={'stage_event': 'stage_enter', 'actor_type': 'recruiter'},
            execution_order=1,
            run_mode='immediate',
            is_active=True,
        )
        WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Create Review Task',
            action_type='create_task',
            action_config={'stage_event': 'stage_enter', 'title': 'Review candidate profile'},
            execution_order=2,
            run_mode='immediate',
            is_active=True,
        )

        result = WorkflowActionHandlersEngine.execute_stage_actions(
            instance=self.instance,
            stage_execution=self.stage_execution,
            stage_event='stage_enter',
        )

        logs = list(WorkflowActionExecutionLog.objects.filter(workflow_instance=self.instance).order_by('created_at'))
        assert result['executed'] == 2
        assert len(logs) == 2
        assert logs[0].action_type == 'assign_actor'
        assert logs[1].action_type == 'create_task'
        assert WorkflowActorAssignment.objects.filter(workflow_instance=self.instance, status='active').exists()

    def test_2_create_interview_action_creates_interview(self):
        action = WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Create Interview',
            action_type='create_interview',
            action_config={'stage_event': 'stage_enter', 'interview_type': 'panel', 'status': 'scheduled'},
            execution_order=1,
            run_mode='immediate',
            is_active=True,
        )

        log = WorkflowActionHandlersEngine.execute_action(
            instance=self.instance,
            stage_execution=self.stage_execution,
            action_definition=action,
        )
        self.instance.refresh_from_db()

        assert log.status == 'completed'
        assert (self.instance.context_data.get('interviews') or [])[0]['status'] == 'scheduled'

    def test_3_generate_document_offer_letter_logged(self):
        action = WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Generate Offer Letter',
            action_type='generate_document',
            action_config={'stage_event': 'stage_enter', 'template_key': 'offer_letter_template'},
            execution_order=1,
            run_mode='immediate',
            is_active=True,
        )

        log = WorkflowActionHandlersEngine.execute_action(
            instance=self.instance,
            stage_execution=self.stage_execution,
            action_definition=action,
        )
        self.instance.refresh_from_db()

        documents = self.instance.context_data.get('generated_documents') or []
        assert log.status == 'completed'
        assert len(documents) == 1
        assert documents[0]['template_key'] == 'offer_letter_template'

    def test_4_action_fail_continue_on_error(self):
        WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Failing Document Action',
            action_type='generate_document',
            action_config={
                'stage_event': 'stage_enter',
                'force_error': True,
                'continue_on_error': True,
                'fail_workflow_on_error': False,
            },
            execution_order=1,
            run_mode='immediate',
            is_active=True,
        )
        WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Create Follow-up Task',
            action_type='create_task',
            action_config={'stage_event': 'stage_enter', 'title': 'Continue processing'},
            execution_order=2,
            run_mode='immediate',
            is_active=True,
        )

        WorkflowActionHandlersEngine.execute_stage_actions(
            instance=self.instance,
            stage_execution=self.stage_execution,
            stage_event='stage_enter',
        )
        self.instance.refresh_from_db()

        logs = list(WorkflowActionExecutionLog.objects.filter(workflow_instance=self.instance).order_by('created_at'))
        assert logs[0].status == 'failed'
        assert logs[1].status == 'completed'
        assert self.instance.status != 'failed'

    def test_5_action_fail_fail_workflow_on_error(self):
        WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Critical Failing Action',
            action_type='generate_document',
            action_config={
                'stage_event': 'stage_enter',
                'force_error': True,
                'continue_on_error': False,
                'fail_workflow_on_error': True,
            },
            execution_order=1,
            run_mode='immediate',
            is_active=True,
        )
        WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Should Not Execute',
            action_type='create_task',
            action_config={'stage_event': 'stage_enter', 'title': 'Do not run'},
            execution_order=2,
            run_mode='immediate',
            is_active=True,
        )

        WorkflowActionHandlersEngine.execute_stage_actions(
            instance=self.instance,
            stage_execution=self.stage_execution,
            stage_event='stage_enter',
        )
        self.instance.refresh_from_db()

        logs = list(WorkflowActionExecutionLog.objects.filter(workflow_instance=self.instance).order_by('created_at'))
        assert logs[0].status == 'failed'
        assert self.instance.status == 'failed'
        assert len(logs) == 1

    def test_6_schedule_action_creates_deferred_log(self):
        action = WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Schedule Delayed Follow-up',
            action_type='schedule_action',
            action_config={
                'stage_event': 'stage_enter',
                'delay_seconds': 600,
                'task_type': 'workflow_resume',
                'payload': {'context': {'source': 'test_schedule_action'}},
            },
            execution_order=1,
            run_mode='immediate',
            is_active=True,
        )

        log = WorkflowActionHandlersEngine.execute_action(
            instance=self.instance,
            stage_execution=self.stage_execution,
            action_definition=action,
        )

        assert log.status == 'deferred'
        assert WorkflowScheduledTask.objects.filter(workflow_instance=self.instance, task_type='workflow_resume').exists()
