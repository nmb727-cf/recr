"""
Cross-Entity Routing Models
============================
Enables workflows to move across entities (company, agency, candidate, HR, HRMS)
while preserving process continuity, tenant safety, and full audit traceability.

Model map:
  WorkflowEntityRoute         — records one cross-entity routing hop
  WorkflowActorAssignment     — who owns / reviews / approves a stage
  WorkflowHandoffCheckpoint   — explicit handoff waiting for an external response
  WorkflowRoutingRule         — per-workflow rules that determine routing targets
  WorkflowRouteTimelineLog    — audit entries per route hop
"""
from django.db import models
from django.utils import timezone
from shared.models import BaseModel
from apps.workflow_execution.models.execution import WorkflowInstance, WorkflowStageExecution


# ---------------------------------------------------------------------------#
# Shared choices                                                               #
# ---------------------------------------------------------------------------#

ENTITY_TYPE_CHOICES = [
    ('company',         'Company'),
    ('agency',          'Agency'),
    ('candidate',       'Candidate'),
    ('recruiter',       'Recruiter'),
    ('hiring_manager',  'Hiring Manager'),
    ('hr',              'HR'),
    ('interviewer',     'Interviewer'),
    ('panel',           'Interview Panel'),
    ('onboarding',      'Onboarding'),
    ('hrms',            'HRMS'),
]

ACTOR_TYPE_CHOICES = [
    ('recruiter',         'Recruiter'),
    ('hiring_manager',    'Hiring Manager'),
    ('hr',                'HR'),
    ('agency_manager',    'Agency Manager'),
    ('agency_recruiter',  'Agency Recruiter'),
    ('interviewer',       'Interviewer'),
    ('candidate',         'Candidate'),
    ('system',            'System'),
]

HANDOFF_TYPE_CHOICES = [
    ('agency_to_company',    'Agency → Company'),
    ('company_to_agency',    'Company → Agency'),
    ('company_to_candidate', 'Company → Candidate'),
    ('candidate_to_company', 'Candidate → Company'),
    ('company_to_hr',        'Company → HR'),
    ('workflow_to_hrms',     'Workflow → HRMS'),
    ('recruiter_to_manager', 'Recruiter → Hiring Manager'),
    ('manager_to_hr',        'Manager → HR'),
]


# ---------------------------------------------------------------------------#
# Model 1 – WorkflowEntityRoute                                               #
# Records one cross-entity routing hop within a workflow instance.            #
# ---------------------------------------------------------------------------#

class WorkflowEntityRoute(BaseModel):
    ROUTE_TYPES = [
        ('ownership_transfer',    'Ownership Transfer'),
        ('action_handoff',        'Action Handoff'),
        ('approval_handoff',      'Approval Handoff'),
        ('scheduling_handoff',    'Scheduling Handoff'),
        ('communication_handoff', 'Communication Handoff'),
        ('onboarding_handoff',    'Onboarding Handoff'),
        ('workflow_continuation', 'Workflow Continuation'),
    ]
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('failed',    'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    workflow_instance  = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='entity_routes')
    from_entity_type   = models.CharField(max_length=32, choices=ENTITY_TYPE_CHOICES)
    from_entity_id     = models.UUIDField(null=True, blank=True)
    to_entity_type     = models.CharField(max_length=32, choices=ENTITY_TYPE_CHOICES)
    to_entity_id       = models.UUIDField(null=True, blank=True)
    route_type         = models.CharField(max_length=32, choices=ROUTE_TYPES, default='workflow_continuation')
    route_reason       = models.TextField(blank=True)
    status             = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True)
    stage_id           = models.UUIDField(null=True, blank=True, db_index=True)  # stage that triggered this
    completed_at       = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'wf_exec_entity_routes'
        ordering = ['-created_at']

    def complete(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def fail(self, reason=''):
        self.status = 'failed'
        self.route_reason = f"{self.route_reason}\nFAIL: {reason}".strip()
        self.save(update_fields=['status', 'route_reason', 'updated_at'])


# ---------------------------------------------------------------------------#
# Model 2 – WorkflowActorAssignment                                           #
# Tracks who is responsible for a specific stage in the workflow instance.    #
# ---------------------------------------------------------------------------#

class WorkflowActorAssignment(BaseModel):
    ASSIGNMENT_TYPES = [
        ('responsible',  'Responsible'),
        ('reviewer',     'Reviewer'),
        ('approver',     'Approver'),
        ('scheduler',    'Scheduler'),
        ('coordinator',  'Coordinator'),
        ('observer',     'Observer'),
    ]
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('revoked',   'Revoked'),
        ('expired',   'Expired'),
    ]
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='actor_assignments')
    stage_id          = models.UUIDField(db_index=True)
    actor_type        = models.CharField(max_length=32, choices=ACTOR_TYPE_CHOICES, db_index=True)
    actor_id          = models.UUIDField(null=True, blank=True, db_index=True)
    assignment_type   = models.CharField(max_length=16, choices=ASSIGNMENT_TYPES, default='responsible')
    assigned_at       = models.DateTimeField(auto_now_add=True)
    status            = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active', db_index=True)
    notes             = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_actor_assignments'
        ordering = ['-assigned_at']

    def complete(self):
        self.status = 'completed'
        self.save(update_fields=['status', 'updated_at'])

    def revoke(self):
        self.status = 'revoked'
        self.save(update_fields=['status', 'updated_at'])


# ---------------------------------------------------------------------------#
# Model 3 – WorkflowHandoffCheckpoint                                         #
# Explicit handoff waiting on an external actor or system response.           #
# ---------------------------------------------------------------------------#

class WorkflowHandoffCheckpoint(BaseModel):
    STATUS_CHOICES = [
        ('pending',      'Pending'),
        ('delivered',    'Delivered'),
        ('acknowledged', 'Acknowledged'),
        ('completed',    'Completed'),
        ('failed',       'Failed'),
        ('expired',      'Expired'),
    ]
    workflow_instance      = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='handoff_checkpoints')
    stage_execution        = models.ForeignKey(WorkflowStageExecution, on_delete=models.SET_NULL, null=True, blank=True, related_name='handoff_checkpoints')
    handoff_from           = models.CharField(max_length=64)   # e.g. "company_recruiter"
    handoff_to             = models.CharField(max_length=64)   # e.g. "agency_recruiter"
    handoff_type           = models.CharField(max_length=32, choices=HANDOFF_TYPE_CHOICES)
    payload                = models.JSONField(default=dict, blank=True)
    expected_response_event = models.CharField(max_length=128, blank=True)
    status                 = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True)
    responded_at           = models.DateTimeField(null=True, blank=True)
    response_payload       = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_exec_handoff_checkpoints'
        ordering = ['-created_at']

    def acknowledge(self, response_payload=None):
        self.status = 'acknowledged'
        self.responded_at = timezone.now()
        if response_payload:
            self.response_payload = response_payload
        self.save(update_fields=['status', 'responded_at', 'response_payload', 'updated_at'])

    def complete(self, response_payload=None):
        self.status = 'completed'
        self.responded_at = self.responded_at or timezone.now()
        if response_payload:
            self.response_payload = response_payload
        self.save(update_fields=['status', 'responded_at', 'response_payload', 'updated_at'])

    def fail(self, reason=''):
        self.status = 'failed'
        self.save(update_fields=['status', 'updated_at'])


# ---------------------------------------------------------------------------#
# Model 4 – WorkflowRoutingRule                                               #
# Per-workflow rules that dynamically determine which entity/actor handles    #
# a stage based on context conditions.                                        #
# ---------------------------------------------------------------------------#

class WorkflowRoutingRule(BaseModel):
    workflow_id          = models.UUIDField(db_index=True)
    stage_id             = models.UUIDField(null=True, blank=True, db_index=True)  # None = applies to all stages
    condition_config     = models.JSONField(default=dict, blank=True)
    # same format as WorkflowStageTransition.condition_config
    route_to_entity_type = models.CharField(max_length=32, choices=ENTITY_TYPE_CHOICES)
    route_to_actor_type  = models.CharField(max_length=32, blank=True)
    route_config         = models.JSONField(default=dict, blank=True)
    # route_config can include: { "handoff_type": "...", "expected_response_event": "...", "assignment_type": "..." }
    priority             = models.IntegerField(default=0)
    label                = models.CharField(max_length=128, blank=True)
    is_active            = models.BooleanField(default=True)

    class Meta:
        db_table = 'wf_exec_routing_rules'
        ordering = ['priority', 'created_at']


# ---------------------------------------------------------------------------#
# Model 5 – WorkflowRouteTimelineLog                                          #
# Audit entry for each routing event within an instance.                      #
# ---------------------------------------------------------------------------#

class WorkflowRouteTimelineLog(BaseModel):
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='route_timeline')
    route             = models.ForeignKey(WorkflowEntityRoute, on_delete=models.SET_NULL, null=True, blank=True, related_name='timeline_logs')
    action            = models.CharField(max_length=255)
    from_actor        = models.CharField(max_length=128, blank=True)
    to_actor          = models.CharField(max_length=128, blank=True)
    reason            = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_route_timeline'
        ordering = ['-created_at']
