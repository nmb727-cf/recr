from rest_framework import generics, permissions
from apps.core.responses import success_response, error_response
from apps.tenants.models import Client
from apps.accounts.models import CustomUser
from apps.organisations.models import Department, Location, Team
from .serializers import OrganisationSerializer, DepartmentSerializer, LocationSerializer, TeamSerializer
from apps.accounts.serializers import CustomUserSerializer  # Import CustomUserSerializer

class IsAuthenticated(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and hasattr(request.user, 'tenant_id')

class OrganisationProfileView(generics.RetrieveUpdateAPIView):
    queryset = Client.objects.filter(is_deleted=False)
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.user.tenant_id)

class UserListView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.filter(is_deleted=False)
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.user.tenant_id)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.filter(is_deleted=False)
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.user.tenant_id)

class DepartmentListView(generics.ListCreateAPIView):
    queryset = Department.objects.filter(is_deleted=False)
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.user.tenant_id)

class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.filter(is_deleted=False)
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.user.tenant_id)

class LocationListView(generics.ListCreateAPIView):
    queryset = Location.objects.filter(is_deleted=False)
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.user.tenant_id)

class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Location.objects.filter(is_deleted=False)
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.user.tenant_id)

class TeamListView(generics.ListCreateAPIView):
    queryset = Team.objects.filter(is_deleted=False)
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.user.tenant_id)

class TeamDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Team.objects.filter(is_deleted=False)
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.user.tenant_id)
