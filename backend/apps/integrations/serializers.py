from rest_framework import serializers
from apps.integrations.models import Integration

class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at', 'updated_at')
