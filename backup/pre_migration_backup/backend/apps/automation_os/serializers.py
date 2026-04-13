from rest_framework import serializers
from apps.automation_os.models import (
    AutomationRuntimeState,
    AutomationEngineRegistry,
    AutomationExecutionPolicy,
    AutomationWorkloadBucket,
    AutomationBusinessCoverage,
    AutomationOperatingEvent,
    AutomationOperatingInsight
)

class AutomationRuntimeStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationRuntimeState
        fields = '__all__'

class AutomationEngineRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationEngineRegistry
        fields = '__all__'

class AutomationExecutionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationExecutionPolicy
        fields = '__all__'

class AutomationWorkloadBucketSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationWorkloadBucket
        fields = '__all__'

class AutomationBusinessCoverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationBusinessCoverage
        fields = '__all__'

class AutomationOperatingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationOperatingEvent
        fields = '__all__'

class AutomationOperatingInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationOperatingInsight
        fields = '__all__'
