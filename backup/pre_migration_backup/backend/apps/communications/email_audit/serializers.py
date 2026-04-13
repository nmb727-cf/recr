from rest_framework import serializers

from apps.communications.models import EmailDeliveryEvent, EmailUsageAudit


class EmailUsageAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUsageAudit
        fields = '__all__'


class EmailDeliveryEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailDeliveryEvent
        fields = '__all__'
