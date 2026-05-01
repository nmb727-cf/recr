from django.db import models
from shared.models import BaseModel

class AutomationSystemReadiness(BaseModel):
    STATUS_CHOICES = [
        ('not_ready', 'Not Ready'),
        ('partial', 'Partial'),
        ('ready_with_warnings', 'Ready with Warnings'),
        ('production_ready', 'Production Ready'),
    ]
    readiness_score = models.IntegerField(default=0)
    readiness_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='not_ready')
    engine_integration_score = models.IntegerField(default=0)
    governance_score = models.IntegerField(default=0)
    reliability_score = models.IntegerField(default=0)
    intelligence_score = models.IntegerField(default=0)
    security_score = models.IntegerField(default=0)
    tenant_isolation_score = models.IntegerField(default=0)
    documentation_score = models.IntegerField(default=0)
    qa_score = models.IntegerField(default=0)

    class Meta:
        db_table = 'automation_system_readiness'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Readiness: {self.readiness_score} ({self.readiness_status})"

class AutomationCompletionCheck(BaseModel):
    CATEGORY_CHOICES = [
        ('engine_integration', 'Engine Integration'),
        ('api', 'API'),
        ('ui', 'UI'),
        ('governance', 'Governance'),
        ('reliability', 'Reliability'),
        ('permissions', 'Permissions'),
        ('tenant_isolation', 'Tenant Isolation'),
        ('analytics', 'Analytics'),
        ('ai', 'AI'),
        ('documentation', 'Documentation'),
        ('qa', 'QA'),
    ]
    STATUS_CHOICES = [
        ('passed', 'Passed'),
        ('warning', 'Warning'),
        ('failed', 'Failed'),
        ('not_run', 'Not Run'),
    ]
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    check_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    check_name = models.CharField(max_length=255)
    check_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_run')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    result_summary = models.TextField(blank=True)
    remediation_action = models.TextField(blank=True)

    class Meta:
        db_table = 'automation_completion_checks'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Check: {self.check_name} ({self.check_status})"

class AutomationGapItem(BaseModel):
    GAP_TYPES = [
        ('missing_integration', 'Missing Integration'),
        ('broken_flow', 'Broken Flow'),
        ('missing_permission', 'Missing Permission'),
        ('missing_audit', 'Missing Audit'),
        ('missing_observability', 'Missing Observability'),
        ('missing_recovery', 'Missing Recovery'),
        ('missing_ui', 'Missing UI'),
        ('missing_api', 'Missing API'),
        ('missing_test', 'Missing Test'),
        ('missing_documentation', 'Missing Documentation'),
    ]
    IMPACT_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('fixed', 'Fixed'),
        ('ignored', 'Ignored'),
    ]
    gap_type = models.CharField(max_length=50, choices=GAP_TYPES)
    module_scope = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField()
    impact_level = models.CharField(max_length=20, choices=IMPACT_LEVELS)
    recommended_fix = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    class Meta:
        db_table = 'automation_gap_items'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class AutomationProductionGate(BaseModel):
    GATE_TYPES = [
        ('governance_gate', 'Governance Gate'),
        ('reliability_gate', 'Reliability Gate'),
        ('security_gate', 'Security Gate'),
        ('isolation_gate', 'Isolation Gate'),
        ('observability_gate', 'Observability Gate'),
        ('qa_gate', 'QA Gate'),
        ('documentation_gate', 'Documentation Gate'),
        ('executive_gate', 'Executive Gate'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('blocked', 'Blocked'),
        ('failed', 'Failed'),
    ]
    gate_name = models.CharField(max_length=255)
    gate_type = models.CharField(max_length=50, choices=GATE_TYPES)
    required = models.BooleanField(default=True)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    blocking_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'automation_production_gates'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.gate_name} - {self.current_status}"

class AutomationCompletionReport(BaseModel):
    REPORT_TYPES = [
        ('readiness_summary', 'Readiness Summary'),
        ('gap_report', 'Gap Report'),
        ('integration_report', 'Integration Report'),
        ('qa_report', 'QA Report'),
        ('production_launch_report', 'Production Launch Report'),
        ('executive_completion_report', 'Executive Completion Report'),
    ]
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    report_name = models.CharField(max_length=255)
    report_payload = models.JSONField(default=dict)
    generated_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'automation_completion_reports'
        ordering = ['-created_at']

    def __str__(self):
        return self.report_name
