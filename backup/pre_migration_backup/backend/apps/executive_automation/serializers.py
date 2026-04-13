from rest_framework import serializers
from .models import (
    ExecutiveAutomationSummary,
    ExecutiveAutomationROI,
    ExecutiveAutomationRisk,
    ExecutiveAutomationDepartment,
    ExecutiveAutomationOpportunity,
)


class ExecutiveAutomationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveAutomationSummary
        fields = [
            'id', 'snapshot_date',
            'total_workflows', 'active_workflows',
            'total_executions_today', 'successful_executions_today',
            'automation_coverage_percent', 'automation_maturity_level',
            'time_saved_hours', 'tasks_automated',
            'sla_improvement_percent', 'open_risks', 'open_opportunities',
            'business_impact_score', 'created_at',
        ]


class ExecutiveAutomationROISerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveAutomationROI
        fields = [
            'id', 'period', 'period_start', 'period_end',
            'hours_saved', 'manual_tasks_reduced',
            'operational_cost_reduction', 'productivity_gain_percent',
            'executions_count', 'success_rate', 'created_at',
        ]


class ExecutiveAutomationRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveAutomationRisk
        fields = [
            'id', 'risk_type', 'severity', 'affected_module',
            'title', 'description', 'status', 'metric_value',
            'created_at', 'updated_at',
        ]


class RiskStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['acknowledged', 'mitigated', 'resolved', 'ignored'])


class ExecutiveAutomationDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveAutomationDepartment
        fields = [
            'id', 'snapshot_date', 'department_name',
            'automation_coverage', 'adoption_score', 'maturity_level',
            'manual_gap_percent', 'workflow_count', 'executions_30d',
            'created_at',
        ]


class ExecutiveAutomationOpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveAutomationOpportunity
        fields = [
            'id', 'opportunity_type', 'module', 'title',
            'description', 'expected_impact', 'priority', 'status',
            'assigned_to', 'source_data', 'created_at', 'updated_at',
        ]


class OpportunityStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['assigned', 'in_progress', 'completed', 'dismissed'])
    assigned_to = serializers.UUIDField(required=False, allow_null=True)
