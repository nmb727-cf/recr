from rest_framework import serializers
from apps.automation_sandbox.models import (
    WorkflowSandboxRun,
    WorkflowSandboxStepLog,
    WorkflowSandboxScenario,
    WorkflowSandboxArtifact,
    WorkflowSandboxApproval,
)

class WorkflowSandboxStepLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSandboxStepLog
        fields = '__all__'

class WorkflowSandboxArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSandboxArtifact
        fields = '__all__'

class WorkflowSandboxRunSerializer(serializers.ModelSerializer):
    steps = WorkflowSandboxStepLogSerializer(many=True, read_only=True)
    artifacts = WorkflowSandboxArtifactSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkflowSandboxRun
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at', 'updated_at', 'status', 'started_at', 'completed_at', 'actual_outcome')

class WorkflowSandboxScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSandboxScenario
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at', 'updated_at', 'is_system_scenario')

class WorkflowSandboxApprovalSerializer(serializers.ModelSerializer):
    run_name = serializers.CharField(source='sandbox_run.run_name', read_only=True)
    
    class Meta:
        model = WorkflowSandboxApproval
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at', 'reviewed_by', 'approved_at')
