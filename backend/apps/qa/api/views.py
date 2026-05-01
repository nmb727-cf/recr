from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.qa.models import (
    ModuleReadinessResult,
    ReadinessBlocker,
    EndToEndScenarioResult
)
from .serializers import (
    ModuleReadinessResultSerializer,
    ReadinessBlockerSerializer,
    EndToEndScenarioResultSerializer
)

class ModuleReadinessResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ModuleReadinessResult.objects.all()
    serializer_class = ModuleReadinessResultSerializer
    
    def get_queryset(self):
        # We might want to filter by tenant_id or user. In our setup, often schemas handle this, but let's be safe.
        return super().get_queryset()

class ReadinessBlockerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReadinessBlocker.objects.all()
    serializer_class = ReadinessBlockerSerializer

class EndToEndScenarioResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EndToEndScenarioResult.objects.all()
    serializer_class = EndToEndScenarioResultSerializer
