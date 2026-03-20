from rest_framework import serializers
from apps.organisations.models import Organisation, Department, Location, Team


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = [
            'id', 'tenant_id', 'name', 'org_type', 'website', 'logo_url',
            'industry', 'size_range', 'country_code', 'timezone',
            'address_line1', 'address_line2', 'city', 'state', 'country',
            'postal_code', 'cin', 'gst_number', 'registration_number',
            'settings', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = [
            'id', 'tenant_id', 'name', 'parent_department_id',
            'head_user_id', 'description', 'is_active',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            'id', 'tenant_id', 'name', 'address_line1', 'address_line2',
            'city', 'state', 'country', 'postal_code',
            'latitude', 'longitude', 'is_headquarters', 'is_active',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = [
            'id', 'tenant_id', 'name', 'department_id', 'location_id',
            'team_lead_id', 'description', 'is_active',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']