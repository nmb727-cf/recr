from rest_framework import serializers
from apps.organisations.models import Organisation, Department, Location, Team, TeamMembership
from apps.accounts.models import CustomUser


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = [
            'id', 'tenant_id', 'name', 'org_type', 'website', 'logo_url',
            'industry', 'size_range', 'country_code', 'primary_language',
            'primary_currency', 'timezone',
            'address_line1', 'address_line2', 'city', 'state', 'country',
            'postal_code', 'cin', 'gst_number', 'registration_number',
            'settings', 'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    parent_department_id = serializers.PrimaryKeyRelatedField(
        source='parent',
        queryset=Department.objects.all(),
        required=False,
        allow_null=True
    )
    head_user_id = serializers.PrimaryKeyRelatedField(
        source='head_user',
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )

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
    department_id = serializers.PrimaryKeyRelatedField(
        source='department',
        queryset=Department.objects.all(),
        required=False,
        allow_null=True
    )
    location_id = serializers.PrimaryKeyRelatedField(
        source='location',
        queryset=Location.objects.all(),
        required=False,
        allow_null=True
    )
    team_lead_id = serializers.PrimaryKeyRelatedField(
        source='team_lead',
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Team
        fields = [
            'id', 'tenant_id', 'name', 'department_id', 'location_id',
            'team_lead_id', 'description', 'is_active',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']


class TeamMembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = TeamMembership
        fields = ['id', 'tenant_id', 'team', 'user_id', 'role', 'created_at']
        read_only_fields = ['id', 'tenant_id', 'created_at']


class HierarchySetupSerializer(serializers.Serializer):
    locations = LocationSerializer(many=True, required=False)
    departments = DepartmentSerializer(many=True, required=False)
    teams = TeamSerializer(many=True, required=False)