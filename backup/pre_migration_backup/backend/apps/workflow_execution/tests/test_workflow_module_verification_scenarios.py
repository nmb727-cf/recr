import uuid

from django.test import TestCase

from apps.orchestration_center.models.event_trigger import WorkflowEventDefinition, WorkflowEventSubscription
from apps.orchestration_center.models.workflow import Workflow, WorkflowEdge, WorkflowNode
from apps.workflow_execution.models import (
    WorkflowActionDefinition,
    WorkflowInstance,
    WorkflowTimeline,
    WorkflowWaitState,
)
from apps.workflow_execution.services.workflow_event_listener import WorkflowEventListener


class TestWorkflowModuleVerificationScenarios(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()

    def _subscribe_event(self, *, workflow, event_key: str, event_name: str, module_scope: str):
        event_def, _ = WorkflowEventDefinition.objects.get_or_create(
            event_key=event_key,
            defaults={
                'event_name': event_name,
                'module_scope': module_scope,
                'description': event_name,
                'payload_schema': {},
                'is_active': True,
            },
        )
        WorkflowEventSubscription.objects.create(
            tenant_id=self.tenant_id,
            workflow=workflow,
            event_definition=event_def,
            trigger_filters={},
            is_active=True,
        )

    def test_scenario_1_company_hiring_flow(self):
        workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='QA Scenario 1 Company Hiring',
            trigger_event='scenario_company_job_created',
            status='active',
            is_active=True,
        )

        start = WorkflowNode.objects.create(workflow=workflow, node_type='start', config={'label': 'Start Hiring'})
        review = WorkflowNode.objects.create(workflow=workflow, node_type='action', config={'label': 'Candidate Review'})
        interview = WorkflowNode.objects.create(workflow=workflow, node_type='action', config={'label': 'Interview'})
        offer = WorkflowNode.objects.create(workflow=workflow, node_type='action', config={'label': 'Offer'})
        onboarding = WorkflowNode.objects.create(workflow=workflow, node_type='action', config={'label': 'Onboarding'})
        end = WorkflowNode.objects.create(workflow=workflow, node_type='end', config={'label': 'End Hiring'})

        WorkflowEdge.objects.create(workflow=workflow, source_node=start, target_node=review)
        WorkflowEdge.objects.create(workflow=workflow, source_node=review, target_node=interview)
        WorkflowEdge.objects.create(workflow=workflow, source_node=interview, target_node=offer)
        WorkflowEdge.objects.create(workflow=workflow, source_node=offer, target_node=onboarding)
        WorkflowEdge.objects.create(workflow=workflow, source_node=onboarding, target_node=end)

        for node in [review, interview, offer, onboarding]:
            WorkflowActionDefinition.objects.create(
                tenant_id=self.tenant_id,
                workflow_id=workflow.id,
                stage_id=node.id,
                action_name=f'Create task for {node.config.get("label", node.node_type)}',
                action_type='create_task',
                action_config={'title': f'{node.config.get("label", node.node_type)} task', 'continue_on_error': True},
                execution_order=1,
                run_mode='immediate',
                is_active=True,
            )

        self._subscribe_event(
            workflow=workflow,
            event_key='scenario_company_job_created',
            event_name='Scenario Company Job Created',
            module_scope='jobs',
        )

        entity_id = uuid.uuid4()
        event_log = WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='scenario_company_job_created',
            entity_type='job',
            entity_id=entity_id,
            payload={'job_title': 'Platform Engineer'},
            source_module='scenario_test',
        )

        instance = WorkflowInstance.objects.get(tenant_id=self.tenant_id, workflow_id=workflow.id, entity_id=entity_id)
        self.assertEqual(event_log.status, 'consumed')
        self.assertEqual(instance.status, 'completed')
        self.assertGreaterEqual(instance.stage_executions.count(), 5)
        self.assertGreaterEqual(instance.action_execution_logs.count(), 4)
        self.assertGreater(WorkflowTimeline.objects.filter(workflow_instance=instance).count(), 0)

    def test_scenario_2_agency_to_company_flow_with_wait_resume(self):
        workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='QA Scenario 2 Agency to Company',
            trigger_event='scenario_agency_submission_received',
            status='active',
            is_active=True,
        )

        start = WorkflowNode.objects.create(workflow=workflow, node_type='start', config={'label': 'Agency Submit'})
        company_review = WorkflowNode.objects.create(workflow=workflow, node_type='action', config={'label': 'Company Review'})
        approval_wait = WorkflowNode.objects.create(
            workflow=workflow,
            node_type='approval',
            config={
                'label': 'Company Approval',
                'wait_reason': 'Waiting for company review approval',
                'resume_event': 'scenario_company_review_approved',
            },
        )
        interview_coord = WorkflowNode.objects.create(workflow=workflow, node_type='action', config={'label': 'Interview Coordination'})
        offer = WorkflowNode.objects.create(workflow=workflow, node_type='action', config={'label': 'Offer'})
        end = WorkflowNode.objects.create(workflow=workflow, node_type='end', config={'label': 'End'})

        WorkflowEdge.objects.create(workflow=workflow, source_node=start, target_node=company_review)
        WorkflowEdge.objects.create(workflow=workflow, source_node=company_review, target_node=approval_wait)
        WorkflowEdge.objects.create(workflow=workflow, source_node=approval_wait, target_node=interview_coord)
        WorkflowEdge.objects.create(workflow=workflow, source_node=interview_coord, target_node=offer)
        WorkflowEdge.objects.create(workflow=workflow, source_node=offer, target_node=end)

        for node in [company_review, interview_coord, offer]:
            WorkflowActionDefinition.objects.create(
                tenant_id=self.tenant_id,
                workflow_id=workflow.id,
                stage_id=node.id,
                action_name=f'Create task for {node.config.get("label", node.node_type)}',
                action_type='create_task',
                action_config={'title': f'{node.config.get("label", node.node_type)} task', 'continue_on_error': True},
                execution_order=1,
                run_mode='immediate',
                is_active=True,
            )

        self._subscribe_event(
            workflow=workflow,
            event_key='scenario_agency_submission_received',
            event_name='Scenario Agency Submission Received',
            module_scope='agency',
        )

        WorkflowEventDefinition.objects.get_or_create(
            event_key='scenario_company_review_approved',
            defaults={
                'event_name': 'Scenario Company Review Approved',
                'module_scope': 'agency',
                'description': 'Resume event for scenario 2',
                'payload_schema': {},
                'is_active': True,
            },
        )

        entity_id = uuid.uuid4()
        start_log = WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='scenario_agency_submission_received',
            entity_type='submission',
            entity_id=entity_id,
            payload={'source': 'agency'},
            source_module='scenario_test',
        )

        instance = WorkflowInstance.objects.get(tenant_id=self.tenant_id, workflow_id=workflow.id, entity_id=entity_id)
        waiting_count = WorkflowWaitState.objects.filter(workflow_instance=instance, status='waiting').count()
        self.assertEqual(start_log.status, 'consumed')
        self.assertEqual(instance.status, 'waiting')
        self.assertGreater(waiting_count, 0)

        resume_log = WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='scenario_company_review_approved',
            entity_type='submission',
            entity_id=entity_id,
            payload={'approval_result': 'approved'},
            source_module='scenario_test',
        )
        instance.refresh_from_db()

        self.assertEqual(resume_log.status, 'consumed')
        self.assertEqual(instance.status, 'completed')
        self.assertGreater(WorkflowWaitState.objects.filter(workflow_instance=instance, status='resumed').count(), 0)
        self.assertGreater(WorkflowTimeline.objects.filter(workflow_instance=instance).count(), 0)

    def test_scenario_3_offer_to_onboarding_handoff_flow(self):
        workflow = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='QA Scenario 3 Offer to Onboarding',
            trigger_event='scenario_offer_accepted',
            status='active',
            is_active=True,
        )

        start = WorkflowNode.objects.create(workflow=workflow, node_type='start', config={'label': 'Offer Accepted'})
        onboarding = WorkflowNode.objects.create(workflow=workflow, node_type='action', config={'label': 'Onboarding'})
        handoff = WorkflowNode.objects.create(workflow=workflow, node_type='action', config={'label': 'HRMS Handoff'})
        end = WorkflowNode.objects.create(workflow=workflow, node_type='end', config={'label': 'End'})

        WorkflowEdge.objects.create(workflow=workflow, source_node=start, target_node=onboarding)
        WorkflowEdge.objects.create(workflow=workflow, source_node=onboarding, target_node=handoff)
        WorkflowEdge.objects.create(workflow=workflow, source_node=handoff, target_node=end)

        WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            stage_id=onboarding.id,
            action_name='Create onboarding SLA',
            action_type='create_sla',
            action_config={'sla_duration_hours': 24, 'warning_duration_hours': 12, 'escalation_duration_hours': 24, 'continue_on_error': True},
            execution_order=1,
            run_mode='immediate',
            is_active=True,
        )
        WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            stage_id=handoff.id,
            action_name='Create HR handoff',
            action_type='create_handoff',
            action_config={'to_entity_type': 'hr', 'to_entity_id': str(uuid.uuid4()), 'handoff_type': 'hrms_handoff', 'continue_on_error': True},
            execution_order=1,
            run_mode='immediate',
            is_active=True,
        )

        self._subscribe_event(
            workflow=workflow,
            event_key='scenario_offer_accepted',
            event_name='Scenario Offer Accepted',
            module_scope='offers',
        )

        entity_id = uuid.uuid4()
        event_log = WorkflowEventListener.receive_event(
            tenant_id=self.tenant_id,
            event_key='scenario_offer_accepted',
            entity_type='offer',
            entity_id=entity_id,
            payload={'offer_status': 'accepted'},
            source_module='scenario_test',
        )

        instance = WorkflowInstance.objects.get(tenant_id=self.tenant_id, workflow_id=workflow.id, entity_id=entity_id)

        self.assertEqual(event_log.status, 'consumed')
        self.assertEqual(instance.status, 'completed')
        self.assertGreaterEqual(instance.action_execution_logs.count(), 2)
        self.assertGreater(WorkflowTimeline.objects.filter(workflow_instance=instance).count(), 0)
