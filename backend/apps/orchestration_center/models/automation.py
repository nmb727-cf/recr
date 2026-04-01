from django.db import models

from shared.models import BaseModel
from apps.orchestration_center.constants.execution_statuses import ApprovalMode, AutomationExecutionStatus, AutomationRuleStatus, ScheduledActionStatus


class AutomationRule(BaseModel):
    rule_key = models.CharField(max_length=128, db_index=True)
    rule_title = models.CharField(max_length=255)
    module_scope = models.CharField(max_length=64, db_index=True)
    trigger_event = models.CharField(max_length=128, db_index=True)
    mode = models.CharField(max_length=32, choices=ApprovalMode.choices, default=ApprovalMode.SUGGESTION_ONLY)
    status = models.CharField(max_length=32, choices=AutomationRuleStatus.choices, default=AutomationRuleStatus.DRAFT, db_index=True)
    is_builtin = models.BooleanField(default=False)
    dry_run_enabled = models.BooleanField(default=False)
    requires_high_risk_approval = models.BooleanField(default=False)
    max_executions_per_day = models.IntegerField(null=True, blank=True)
    duplicate_window_seconds = models.IntegerField(default=300)
    priority_order = models.PositiveSmallIntegerField(default=100, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_automation_rules'
        ordering = ['priority_order', 'rule_title']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'rule_key'],
                condition=models.Q(is_deleted=False),
                name='uniq_icc_automation_rule_tenant_key_active',
            ),
        ]

    def __str__(self):
        return self.rule_title


class AutomationRuleCondition(BaseModel):
    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE, related_name='conditions')
    condition_group = models.CharField(max_length=32, default='default')
    field_path = models.CharField(max_length=255)
    operator = models.CharField(max_length=32)
    expected_value_json = models.JSONField(default=dict, blank=True)
    sequence_order = models.PositiveSmallIntegerField(default=1)
    is_negated = models.BooleanField(default=False)

    class Meta:
        db_table = 'icc_automation_rule_conditions'
        ordering = ['condition_group', 'sequence_order']

    def __str__(self):
        return f'{self.rule.rule_key}:{self.field_path}'


class AutomationRuleAction(BaseModel):
    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=64)
    action_config_json = models.JSONField(default=dict, blank=True)
    delay_seconds = models.IntegerField(default=0)
    requires_approval = models.BooleanField(default=False)
    sequence_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = 'icc_automation_rule_actions'
        ordering = ['sequence_order']

    def __str__(self):
        return f'{self.rule.rule_key}:{self.action_type}'


class AutomationRuleScope(BaseModel):
    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE, related_name='scopes')
    entity_type = models.CharField(max_length=64, blank=True)
    stage_key = models.CharField(max_length=64, blank=True)
    role_scope = models.CharField(max_length=64, blank=True)
    source_scope = models.CharField(max_length=64, blank=True)
    working_hours_only = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'icc_automation_rule_scopes'
        ordering = ['-is_active', 'entity_type']

    def __str__(self):
        return f'{self.rule.rule_key}:{self.entity_type or "all"}'


class AutomationExecutionRun(BaseModel):
    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE, related_name='runs')
    source_event = models.CharField(max_length=128, db_index=True)
    source_module = models.CharField(max_length=64, db_index=True)
    source_entity_type = models.CharField(max_length=64, db_index=True)
    source_entity_id = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, choices=AutomationExecutionStatus.choices, default=AutomationExecutionStatus.QUEUED, db_index=True)
    mode = models.CharField(max_length=32, choices=ApprovalMode.choices, default=ApprovalMode.SUGGESTION_ONLY)
    dedupe_key = models.CharField(max_length=255, blank=True, db_index=True)
    trigger_payload_json = models.JSONField(default=dict, blank=True)
    evaluated_conditions_json = models.JSONField(default=list, blank=True)
    action_results_json = models.JSONField(default=list, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    failure_category = models.CharField(max_length=64, blank=True)
    failure_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_automation_execution_runs'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['dedupe_key'],
                condition=~models.Q(dedupe_key=''),
                name='uniq_icc_automation_dedupe_key',
            ),
        ]

    def __str__(self):
        return f'{self.rule.rule_key}:{self.status}'


class AutomationScheduledAction(BaseModel):
    run = models.ForeignKey(AutomationExecutionRun, on_delete=models.CASCADE, related_name='scheduled_actions')
    action_type = models.CharField(max_length=64)
    status = models.CharField(max_length=32, choices=ScheduledActionStatus.choices, default=ScheduledActionStatus.PENDING, db_index=True)
    execute_at = models.DateTimeField(db_index=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    payload_json = models.JSONField(default=dict, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        db_table = 'icc_automation_scheduled_actions'
        ordering = ['execute_at']

    def __str__(self):
        return f'{self.action_type}@{self.execute_at}'

