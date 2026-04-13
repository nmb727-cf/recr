from rest_framework import serializers
from apps.automation_playbooks.models import (
    AutomationPlaybook,
    AutomationPlaybookItem,
    AutomationPlaybookInstall,
    AutomationPlaybookRecommendation,
    AutomationPlaybookAnalytics,
)

class AutomationPlaybookItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationPlaybookItem
        fields = '__all__'

class AutomationPlaybookSerializer(serializers.ModelSerializer):
    items = AutomationPlaybookItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = AutomationPlaybook
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at', 'updated_at', 'created_by', 'is_system_playbook')

class AutomationPlaybookInstallSerializer(serializers.ModelSerializer):
    playbook_name = serializers.CharField(source='playbook.name', read_only=True)
    
    class Meta:
        model = AutomationPlaybookInstall
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at', 'updated_at', 'installed_by', 'installed_at', 'completed_at')

class AutomationPlaybookRecommendationSerializer(serializers.ModelSerializer):
    playbook_name = serializers.CharField(source='playbook.name', read_only=True)
    playbook_category = serializers.CharField(source='playbook.category', read_only=True)
    
    class Meta:
        model = AutomationPlaybookRecommendation
        fields = '__all__'
        read_only_fields = ('id', 'tenant_id', 'created_at')

class AutomationPlaybookAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationPlaybookAnalytics
        fields = '__all__'
