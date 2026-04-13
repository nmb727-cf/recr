from apps.orchestration_center.models import IntelligenceAuditLog


class AuditService:
    @staticmethod
    def log(*, tenant_id=None, actor_id=None, actor_type='user', action_type, target_type, target_id=None, before_state_json=None, after_state_json=None, metadata_json=None):
        return IntelligenceAuditLog.objects.create(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=actor_type,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            before_state_json=before_state_json or {},
            after_state_json=after_state_json or {},
            metadata_json=metadata_json or {},
        )

