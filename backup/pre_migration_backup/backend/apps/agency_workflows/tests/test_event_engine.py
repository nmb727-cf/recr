import uuid
import pytest
from apps.agency_workflows.models import (
    AgencyWorkflowDefinition,
    AgencyWorkflowEventDefinition,
    AgencyWorkflowEventSubscription,
    AgencyWorkflowEventLog,
    AgencyWorkflowEventDebugTrace
)
from apps.agency_workflows.services.agency_workflow_event_engine import AgencyWorkflowEventEngine

@pytest.mark.django_db
class TestAgencyWorkflowEventEngine:
    def setup_method(self):
        self.tenant_id = uuid.uuid4()
        
        # 1. Create Workflow
        self.workflow = AgencyWorkflowDefinition.objects.create(
            tenant_id=self.tenant_id,
            name="Auto-Notify Workflow",
            scope="submission",
            status="active"
        )
        
        # 2. Create Event Definition
        self.event_def = AgencyWorkflowEventDefinition.objects.create(
            event_key="submission_sent",
            event_name="Submission Sent",
            module_scope="submissions"
        )
        
        # 3. Create Subscription
        self.subscription = AgencyWorkflowEventSubscription.objects.create(
            tenant_id=self.tenant_id,
            workflow=self.workflow,
            event_definition=self.event_def,
            trigger_filters={"client_id": "client_abc"}
        )

    def test_emit_event_matching_filters(self):
        # Emit event with matching client_id
        entity_id = uuid.uuid4()
        payload = {"client_id": "client_abc", "candidate_name": "John Doe"}
        
        log = AgencyWorkflowEventEngine.emit_agency_event(
            tenant_id=self.tenant_id,
            event_key="submission_sent",
            entity_type="submission",
            entity_id=entity_id,
            payload=payload,
            source_module="submissions_module"
        )
        
        assert log.status == 'consumed'
        assert AgencyWorkflowEventDebugTrace.objects.filter(event_log=log, decision='executed').exists()

    def test_emit_event_filtered_out(self):
        # Emit event with different client_id
        entity_id = uuid.uuid4()
        payload = {"client_id": "other_client", "candidate_name": "Jane Doe"}
        
        log = AgencyWorkflowEventEngine.emit_agency_event(
            tenant_id=self.tenant_id,
            event_key="submission_sent",
            entity_type="submission",
            entity_id=entity_id,
            payload=payload,
            source_module="submissions_module"
        )
        
        # Should be ignored because filter "client_id": "client_abc" didn't match
        assert log.status == 'ignored'
        assert AgencyWorkflowEventDebugTrace.objects.filter(decision='filtered_out').exists()

    def test_emit_unsubscribed_event(self):
        entity_id = uuid.uuid4()
        log = AgencyWorkflowEventEngine.emit_agency_event(
            tenant_id=self.tenant_id,
            event_key="random_event",
            entity_type="test",
            entity_id=entity_id,
            payload={},
            source_module="test"
        )
        
        assert log.status == 'ignored'
