def tenant_can_use_provider(settings_obj, provider_id):
    allowed = settings_obj.allowed_provider_ids_json or []
    return not allowed or str(provider_id) in [str(value) for value in allowed]

