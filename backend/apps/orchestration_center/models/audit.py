from django.db import models


class IntelligenceAuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    actor_id = models.UUIDField(null=True, blank=True, db_index=True)
    actor_type = models.CharField(max_length=32, db_index=True)
    action_type = models.CharField(max_length=64, db_index=True)
    target_type = models.CharField(max_length=64, db_index=True)
    target_id = models.UUIDField(null=True, blank=True, db_index=True)
    before_state_json = models.JSONField(default=dict, blank=True)
    after_state_json = models.JSONField(default=dict, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'icc_intelligence_audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action_type}:{self.target_type}'

