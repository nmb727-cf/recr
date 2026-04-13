from rest_framework import serializers
from apps.orchestration_center.models.orchestration_engine import (
    WorkflowProcessInstance,
    WorkflowStageExecution,
    WorkflowApprovalCheckpoint,
    WorkflowSchedulerCheckpoint,
    WorkflowNegotiationCheckpoint,
    WorkflowHandoffRecord
)

class WorkflowStageExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStageExecution
        fields = '__all__'

class WorkflowApprovalCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowApprovalCheckpoint
        fields = '__all__'

class WorkflowSchedulerCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSchedulerCheckpoint
        fields = '__all__'

class WorkflowNegotiationCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNegotiationCheckpoint
        fields = '__all__'

class WorkflowHandoffRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowHandoffRecord
        fields = '__all__'

class WorkflowProcessInstanceSerializer(serializers.ModelSerializer):
    stages = WorkflowStageExecutionSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkflowProcessInstance
        fields = '__all__'

class WorkflowProcessTimelineSerializer(serializers.ModelSerializer):
    stages = WorkflowStageExecutionSerializer(many=True, read_only=True)
    approvals = WorkflowApprovalCheckpointSerializer(many=True, read_only=True)
    scheduling = WorkflowSchedulerCheckpointSerializer(many=True, read_only=True, source='scheduling_checkpoints')
    negotiations = WorkflowNegotiationCheckpointSerializer(many=True, read_only=True)
    handoffs = WorkflowHandoffRecordSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowProcessInstance
        fields = ['id', 'workflow_id', 'entity_type', 'entity_id', 'process_status', 'current_stage', 'started_at', 'completed_at', 'stages', 'approvals', 'scheduling', 'negotiations', 'handoffs']
