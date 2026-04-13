from rest_framework import serializers
from ..models.orchestration import (
    AgencyWorkflowProcessInstance,
    AgencyWorkflowStageExecution,
    AgencyInternalApprovalCheckpoint,
    AgencyClientResponseCheckpoint,
    AgencyOfferProgressCheckpoint,
    AgencyPlacementGuaranteeRecord
)

class AgencyWorkflowStageExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyWorkflowStageExecution
        fields = '__all__'

class AgencyInternalApprovalCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyInternalApprovalCheckpoint
        fields = '__all__'

class AgencyClientResponseCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyClientResponseCheckpoint
        fields = '__all__'

class AgencyOfferProgressCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyOfferProgressCheckpoint
        fields = '__all__'

class AgencyPlacementGuaranteeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyPlacementGuaranteeRecord
        fields = '__all__'

class AgencyWorkflowProcessInstanceSerializer(serializers.ModelSerializer):
    stages = AgencyWorkflowStageExecutionSerializer(many=True, read_only=True)
    
    class Meta:
        model = AgencyWorkflowProcessInstance
        fields = '__all__'

class AgencyWorkflowProcessTimelineSerializer(serializers.ModelSerializer):
    stages = AgencyWorkflowStageExecutionSerializer(many=True, read_only=True)
    internal_approvals = AgencyInternalApprovalCheckpointSerializer(many=True, read_only=True)
    client_responses = AgencyClientResponseCheckpointSerializer(many=True, read_only=True)
    offer_checkpoints = AgencyOfferProgressCheckpointSerializer(many=True, read_only=True)
    placement_guarantees = AgencyPlacementGuaranteeRecordSerializer(many=True, read_only=True)

    class Meta:
        model = AgencyWorkflowProcessInstance
        fields = [
            'id', 'workflow_id', 'entity_type', 'entity_id', 'candidate_id', 'client_id', 'job_id', 
            'assigned_recruiter_id', 'process_status', 'current_stage', 'started_at', 'completed_at', 
            'stages', 'internal_approvals', 'client_responses', 'offer_checkpoints', 'placement_guarantees'
        ]
