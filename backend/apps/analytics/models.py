import uuid
from django.db import models
from shared.models import BaseModel

class SystemIntelligenceMemory(BaseModel):
    category = models.CharField(max_length=64, db_index=True) # recruiter, agency, interview, pipeline
    entity_id = models.UUIDField(null=True, blank=True, db_index=True)
    entity_name = models.CharField(max_length=255, blank=True)
    attribute_key = models.CharField(max_length=64, db_index=True) # speed, success_rate, best_role
    attribute_value = models.JSONField(default=dict)
    confidence_score = models.FloatField(default=0.0)
    learned_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'icc_system_intelligence_memory'
        ordering = ['-learned_at']
        verbose_name = "System Intelligence Memory"
        verbose_name_plural = "System Intelligence Memories"

    def __str__(self):
        return f'{self.category}:{self.attribute_key}:{self.entity_name or self.entity_id}'
