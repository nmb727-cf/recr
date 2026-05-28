from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        user_role = getattr(self.request.user, 'role', '')
        if user_role == 'super_admin':
            requested_tenant_id = self.request.query_params.get('tenant_id')
            if requested_tenant_id:
                return qs.filter(tenant_id=requested_tenant_id)
            return qs
        if tenant_id:
            return qs.filter(tenant_id=tenant_id)
        return qs.none()

class ReadinessBlockerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReadinessBlocker.objects.all()
    serializer_class = ReadinessBlockerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        user_role = getattr(self.request.user, 'role', '')
        if user_role == 'super_admin':
            requested_tenant_id = self.request.query_params.get('tenant_id')
            if requested_tenant_id:
                return qs.filter(tenant_id=requested_tenant_id)
            return qs
        if tenant_id:
            return qs.filter(tenant_id=tenant_id)
        return qs.none()

class EndToEndScenarioResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EndToEndScenarioResult.objects.all()
    serializer_class = EndToEndScenarioResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        user_role = getattr(self.request.user, 'role', '')
        if user_role == 'super_admin':
            requested_tenant_id = self.request.query_params.get('tenant_id')
            if requested_tenant_id:
                return qs.filter(tenant_id=requested_tenant_id)
            return qs
        if tenant_id:
            return qs.filter(tenant_id=tenant_id)
        return qs.none()
