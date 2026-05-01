from rest_framework import serializers

from apps.tenants.models import PlatformSetting


class TenantFeatureFlagsUpdateSerializer(serializers.Serializer):
    feature_flags = serializers.DictField(
        child=serializers.BooleanField(),
        allow_empty=True,
    )


class TenantLimitsUpdateSerializer(serializers.Serializer):
    user_limit = serializers.IntegerField(min_value=1, max_value=100000, required=False)
    job_limit = serializers.IntegerField(min_value=1, max_value=1000000, required=False)
    candidate_limit = serializers.IntegerField(min_value=1, max_value=10000000, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one limit value is required.")
        return attrs


class TenantStatusActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class PlatformSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformSetting
        fields = [
            'id',
            'key',
            'category',
            'value_json',
            'description',
            'is_editable',
            'updated_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_by', 'created_at', 'updated_at']


class PlatformSettingsBulkUpdateSerializer(serializers.Serializer):
    settings = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
    )
