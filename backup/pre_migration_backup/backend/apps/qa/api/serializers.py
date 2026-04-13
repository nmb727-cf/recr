from rest_framework import serializers
from apps.qa.models import (
    ModuleReadinessResult,
    ModuleCheckResult,
    EndToEndScenarioResult,
    ReadinessBlocker
)

class ModuleReadinessResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleReadinessResult
        fields = '__all__'

class ReadinessBlockerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadinessBlocker
        fields = '__all__'

class EndToEndScenarioResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = EndToEndScenarioResult
        fields = '__all__'
