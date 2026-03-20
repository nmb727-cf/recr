from rest_framework import serializers
from apps.tenants.models import Client
from apps.accounts.models import CustomUser
from apps.organisations.models import Department, Location, Team

class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'slug', 'tenant_type', 'status', 'country_code', 'timezone', 'logo_url', 'website', 'industry', 'size_range', 'settings', 'created_at']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'tenant_id', 'name', 'parent_department_id', 'head_user_id', 'description', 'is_active', 'created_at']

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'tenant_id', 'name', 'address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code', 'is_headquarters', 'is_active', 'created_at']

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'tenant_id', 'name', 'department_id', 'location_id', 'team_lead_id', 'description', 'is_active', 'created_at']
