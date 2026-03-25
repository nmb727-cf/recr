from .models import TalentPoolActivity


def record_talent_pool_activity(*, talent_pool, event_type, actor=None, payload=None, source='manual'):
    return TalentPoolActivity.objects.create(
        tenant_id=talent_pool.tenant_id,
        talent_pool=talent_pool,
        event_type=event_type,
        actor=actor,
        payload=payload or {},
        source=source,
    )
