import uuid

from django.test import TestCase

from apps.orchestration_center.models.workflow import Workflow, WorkflowNode
from apps.workflow_execution.models import WorkflowActionDefinition
from apps.workflow_execution.services.workflow_instance_tracker import WorkflowInstanceTracker
from apps.workflow_execution.services.workflow_versioning_engine import WorkflowVersioningEngine


def make_workflow(tenant_id):
    workflow = Workflow.objects.create(
        tenant_id=tenant_id,
        name='Versioning WF',
        trigger_event='job_created',
        status='active',
        is_active=True,
    )
    stage = WorkflowNode.objects.create(workflow=workflow, node_type='action', config={'label': 'A'})
    return workflow, stage


class TestWorkflowVersioningEngine(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.workflow, self.stage = make_workflow(self.tenant_id)

    def test_1_user_edits_published_workflow_creates_draft_live_untouched(self):
        initial_draft = WorkflowVersioningEngine.create_draft(workflow_id=self.workflow.id)
        published = WorkflowVersioningEngine.publish_draft(draft=initial_draft, notes='v1 published')

        draft = WorkflowVersioningEngine.create_draft(workflow_id=self.workflow.id)
        WorkflowVersioningEngine.update_draft(draft=draft, name='Edited Draft')

        published.refresh_from_db()
        assert published.status == 'published'
        assert draft.status == 'editing'
        assert draft.version_id != published.id

    def test_2_publish_draft_creates_new_published_version(self):
        v1_draft = WorkflowVersioningEngine.create_draft(workflow_id=self.workflow.id)
        v1 = WorkflowVersioningEngine.publish_draft(draft=v1_draft, notes='v1')

        v2_draft = WorkflowVersioningEngine.create_draft(workflow_id=self.workflow.id)
        v2 = WorkflowVersioningEngine.publish_draft(draft=v2_draft, notes='v2')

        v1.refresh_from_db()
        v2.refresh_from_db()
        assert v2.status == 'published'
        assert v1.status == 'archived'
        assert v2.version_number > v1.version_number

    def test_3_rollback_to_older_version_logged(self):
        v1 = WorkflowVersioningEngine.publish_draft(
            draft=WorkflowVersioningEngine.create_draft(workflow_id=self.workflow.id),
            notes='v1',
        )
        v2 = WorkflowVersioningEngine.publish_draft(
            draft=WorkflowVersioningEngine.create_draft(workflow_id=self.workflow.id),
            notes='v2',
        )

        rolled = WorkflowVersioningEngine.rollback_to_version(
            workflow_id=self.workflow.id,
            version_id=v1.id,
        )

        v2.refresh_from_db()
        rolled.refresh_from_db()
        assert rolled.status == 'published'
        assert v2.status == 'archived'
        assert rolled.change_logs.filter(change_type='rolled_back').exists()

    def test_4_compare_two_versions_generates_diff(self):
        base_draft = WorkflowVersioningEngine.create_draft(workflow_id=self.workflow.id)
        v1 = WorkflowVersioningEngine.publish_draft(draft=base_draft, notes='v1')

        WorkflowActionDefinition.objects.create(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            stage_id=self.stage.id,
            action_name='Create Task Action',
            action_type='create_task',
            action_config={'title': 'Review Candidate'},
            execution_order=1,
            run_mode='immediate',
            is_active=True,
        )
        changed_draft = WorkflowVersioningEngine.create_draft(workflow_id=self.workflow.id)
        WorkflowVersioningEngine.save_draft_snapshot(draft=changed_draft)
        v2 = WorkflowVersioningEngine.publish_draft(draft=changed_draft, notes='v2')

        comparison = WorkflowVersioningEngine.compare_versions(
            workflow_id=self.workflow.id,
            from_version_id=v1.id,
            to_version_id=v2.id,
        )

        assert comparison is not None
        assert 'actions' in comparison.comparison_result
        assert len(comparison.comparison_result['actions']['added']) >= 1

    def test_5_existing_instance_keeps_version_after_new_publish(self):
        v1 = WorkflowVersioningEngine.publish_draft(
            draft=WorkflowVersioningEngine.create_draft(workflow_id=self.workflow.id),
            notes='v1',
        )
        instance_before = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='candidate',
            entity_id=uuid.uuid4(),
            status='running',
        )

        v2 = WorkflowVersioningEngine.publish_draft(
            draft=WorkflowVersioningEngine.create_draft(workflow_id=self.workflow.id),
            notes='v2',
        )
        instance_after = WorkflowInstanceTracker.create_workflow_instance(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow.id,
            entity_type='candidate',
            entity_id=uuid.uuid4(),
            status='running',
        )

        instance_before.refresh_from_db()
        instance_after.refresh_from_db()
        assert str(instance_before.version_id) == str(v1.id)
        assert str(instance_after.version_id) == str(v2.id)
