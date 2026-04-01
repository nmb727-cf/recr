from apps.orchestration_center.models import AIProvider, TenantIntelligenceSettings


class TenantSettingsService:
    @staticmethod
    def get_or_create(tenant_id, created_by=None):
        return TenantIntelligenceSettings.objects.get_or_create(
            tenant_id=tenant_id,
            defaults={
                'created_by': created_by,
                'updated_by_id': created_by,
            },
        )

    @staticmethod
    def update_settings(*, settings_obj, data, updated_by_id):
        allowed_provider_ids = data.get('allowed_provider_ids_json')
        if allowed_provider_ids is not None:
            provider_count = AIProvider.objects.filter(
                id__in=allowed_provider_ids,
                tenant_id__in=[settings_obj.tenant_id, None],
                is_deleted=False,
            ).count()
            if provider_count != len(allowed_provider_ids):
                raise ValueError('allowed_provider_ids_json contains inaccessible providers.')
        for field, value in data.items():
            setattr(settings_obj, field, value)
        settings_obj.updated_by_id = updated_by_id
        settings_obj.save()
        return settings_obj
