from rest_framework import serializers
from apps.automation_sla.models import (
    WorkflowSLAPolicy,
    WorkflowSLAExecution,
    WorkflowSLAReminder,
    WorkflowSLAEscalationRule,
    WorkflowSLABreachInsight,
)

class WorkflowSLAPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSLAPolicy
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at', 'updated_at', 'created_by')

class WorkflowSLAExecutionSerializer(serializers.ModelSerializer):
    policy_name = serializers.CharField(source='sla_policy.name', read_only=True)
    
    class Meta:
        model = WorkflowSLAExecution
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at', 'updated_at')

class WorkflowSLAReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSLAReminder
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at')

class WorkflowSLAEscalationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSLAEscalationRule
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at')

class WorkflowSLABreachInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowSLABreachInsight
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at')
