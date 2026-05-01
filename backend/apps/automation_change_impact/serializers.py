from rest_framework import serializers
from apps.automation_change_impact.models import (
    WorkflowChangeSet,
    WorkflowImpactAnalysis,
    WorkflowDependencyMap,
    WorkflowDeploymentPlan,
    WorkflowRollbackPreview,
)

class WorkflowImpactAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowImpactAnalysis
        fields = '__all__'

class WorkflowDeploymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDeploymentPlan
        fields = '__all__'

class WorkflowRollbackPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRollbackPreview
        fields = '__all__'

class WorkflowChangeSetSerializer(serializers.ModelSerializer):
    impact_analysis = WorkflowImpactAnalysisSerializer(read_only=True)
    deployment_plan = WorkflowDeploymentPlanSerializer(read_only=True)
    rollback_preview = WorkflowRollbackPreviewSerializer(read_only=True)
    
    class Meta:
        model = WorkflowChangeSet
        fields = '__all__'

class WorkflowDependencyMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDependencyMap
        fields = '__all__'
