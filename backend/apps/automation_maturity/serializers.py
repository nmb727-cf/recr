from rest_framework import serializers
from .models import (
    AutomationMaturityAssessment,
    AutomationModuleMaturity,
    AutomationTeamAdoption,
    AutomationMaturityRecommendation,
    AutomationMaturityRoadmap,
    AutomationBusinessTransformationMetric,
)


class AutomationModuleMaturitySerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationModuleMaturity
        fields = [
            'id', 'module_scope', 'maturity_score', 'maturity_level',
            'automation_coverage_percent', 'workflow_count', 'playbook_count',
            'reliability_score', 'governance_score', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AutomationTeamAdoptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationTeamAdoption
        fields = [
            'id', 'team_name', 'department_id', 'adoption_score',
            'active_user_count', 'workflow_usage_count', 'playbook_usage_count',
            'manual_override_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AutomationMaturityAssessmentSerializer(serializers.ModelSerializer):
    module_scores = AutomationModuleMaturitySerializer(many=True, read_only=True)
    team_scores   = AutomationTeamAdoptionSerializer(many=True, read_only=True)

    class Meta:
        model = AutomationMaturityAssessment
        fields = [
            'id', 'tenant_id', 'assessment_date',
            'overall_maturity_score', 'maturity_level',
            'coverage_score', 'adoption_score', 'governance_score',
            'reliability_score', 'intelligence_score', 'operating_score',
            'business_impact_score', 'score_breakdown',
            'created_at', 'module_scores', 'team_scores',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at']


class AutomationMaturityAssessmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list / trend endpoints."""
    class Meta:
        model = AutomationMaturityAssessment
        fields = [
            'id', 'assessment_date', 'overall_maturity_score', 'maturity_level',
            'coverage_score', 'adoption_score', 'governance_score',
            'reliability_score', 'intelligence_score', 'operating_score',
            'business_impact_score', 'created_at',
        ]


class AutomationMaturityRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationMaturityRecommendation
        fields = [
            'id', 'tenant_id', 'recommendation_type', 'title', 'description',
            'target_area', 'expected_maturity_gain', 'priority', 'status',
            'created_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at']


class AutomationMaturityRoadmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationMaturityRoadmap
        fields = [
            'id', 'tenant_id', 'roadmap_name', 'current_level', 'target_level',
            'roadmap_steps', 'expected_timeline_days', 'created_by', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class AutomationBusinessTransformationMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationBusinessTransformationMetric
        fields = [
            'id', 'tenant_id', 'metric_date', 'process_name',
            'manual_effort_reduction_percent', 'response_time_improvement_percent',
            'sla_improvement_percent', 'automation_usage_percent',
            'executions_this_period', 'baseline_executions', 'created_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at']
