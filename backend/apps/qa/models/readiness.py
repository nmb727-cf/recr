import uuid
from django.db import models
from shared.models import BaseModel

class ModuleReadinessResult(BaseModel):
    module_key = models.CharField(max_length=128, db_index=True)
    functional_score = models.IntegerField(default=0)
    integration_score = models.IntegerField(default=0)
    workflow_score = models.IntegerField(default=0)
    overall_score = models.IntegerField(default=0)
    
    FINAL_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_development', 'In Development'),
        ('functional_ready', 'Functional Ready'),
        ('integration_ready', 'Integration Ready'),
        ('workflow_ready', 'Workflow Ready'),
        ('production_ready', 'Production Ready'),
    ]
    final_status = models.CharField(max_length=64, choices=FINAL_STATUS_CHOICES, default='not_started')
    
    blockers_count = models.IntegerField(default=0)
    warnings_count = models.IntegerField(default=0)
    tested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'qa'
        db_table = 'qa_module_readiness_results'
        ordering = ['-tested_at']

class ModuleCheckResult(BaseModel):
    CHECK_TYPE_CHOICES = [
        ('functional', 'Functional'),
        ('integration', 'Integration'),
        ('workflow', 'Workflow'),
        ('end_to_end', 'End to End'),
        ('security', 'Security'),
        ('isolation', 'Isolation'),
    ]
    STATUS_CHOICES = [
        ('passed', 'Passed'),
        ('warning', 'Warning'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    module_key = models.CharField(max_length=128, db_index=True)
    check_type = models.CharField(max_length=32, choices=CHECK_TYPE_CHOICES)
    check_name = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES)
    severity = models.CharField(max_length=32, choices=SEVERITY_CHOICES, default='low')
    
    summary = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True, null=True)
    remediation_hint = models.TextField(blank=True, null=True)
    tested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'qa'
        db_table = 'qa_module_check_results'
        ordering = ['-tested_at']

class EndToEndScenarioResult(BaseModel):
    STATUS_CHOICES = [
        ('passed', 'Passed'),
        ('warning', 'Warning'),
        ('failed', 'Failed'),
    ]
    
    scenario_key = models.CharField(max_length=128, db_index=True)
    scenario_name = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES)
    failed_step = models.CharField(max_length=255, blank=True, null=True)
    summary = models.TextField(blank=True)
    execution_trace = models.JSONField(default=list, blank=True)
    tested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'qa'
        db_table = 'qa_e2e_scenario_results'
        ordering = ['-tested_at']

class ReadinessBlocker(BaseModel):
    BLOCKER_TYPE_CHOICES = [
        ('missing_api', 'Missing API'),
        ('broken_integration', 'Broken Integration'),
        ('missing_event', 'Missing Event'),
        ('missing_permission', 'Missing Permission'),
        ('missing_workflow_support', 'Missing Workflow Support'),
        ('missing_scheduler_logic', 'Missing Scheduler Logic'),
        ('missing_document_generation', 'Missing Document Generation'),
        ('missing_handoff', 'Missing Handoff'),
        ('tenant_isolation_issue', 'Tenant Isolation Issue'),
        ('audit_gap', 'Audit Gap'),
    ]
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    blocker_key = models.CharField(max_length=128, db_index=True)
    module_key = models.CharField(max_length=128, db_index=True)
    blocker_type = models.CharField(max_length=64, choices=BLOCKER_TYPE_CHOICES)
    severity = models.CharField(max_length=32, choices=SEVERITY_CHOICES)
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    recommended_fix = models.TextField(blank=True, null=True)
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'qa'
        db_table = 'qa_readiness_blockers'
        ordering = ['-detected_at']
