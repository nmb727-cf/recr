from django.db import models
from django.utils import timezone
from shared.models import BaseModel

# ---------------------------------------------------------------------------#
# Constants shared across models and the stage engine                         #
# ---------------------------------------------------------------------------#

WAIT_REASON_CHOICES = [
    ('waiting_approval', 'Waiting Approval'),
    ('waiting_candidate', 'Waiting Candidate'),
    ('waiting_client', 'Waiting Client'),
    ('waiting_recruiter', 'Waiting Recruiter'),
    ('waiting_scheduler', 'Waiting Scheduler'),
    ('waiting_signature', 'Waiting Signature'),
    ('waiting_other', 'Waiting Other'),
]

# Maps wait_reason → resume event keys (used by event listener)
WAIT_REASON_RESUME_EVENTS = {
    'waiting_approval':  ['approval_received'],
    'waiting_candidate': [
        'candidate_response_received',
        'offer_accepted',
        'offer_rejected',
        'candidate_interview_confirmed',
        'candidate_interview_declined',
        'candidate_interview_reschedule_requested',
        'offer_counter_received',
    ],
    'waiting_client':    ['client_feedback_received'],
    'waiting_recruiter': ['recruiter_review_completed', 'interview_feedback_submitted'],
    'waiting_scheduler': ['interview_scheduled'],
    'waiting_signature': ['document_signed'],
    'waiting_other':     ['hrms_handoff_rejected'],
}

# Maps WorkflowNode.node_type → WorkflowWaitState.wait_type
NODE_TYPE_TO_WAIT_TYPE = {
    'approval':   'approval',
    'human_task': 'recruiter_review',
    'scheduling': 'interview_schedule',
    'document':   'document_signature',
    'wait':       'manual',
}

# Maps wait_type → WAIT_REASON_CHOICES key (for WorkflowInstance.wait_reason)
WAIT_TYPE_TO_WAIT_REASON = {
    'approval':           'waiting_approval',
    'recruiter_review':   'waiting_recruiter',
    'candidate_response': 'waiting_candidate',
    'client_feedback':    'waiting_client',
    'interview_schedule': 'waiting_scheduler',
    'document_signature': 'waiting_signature',
    'manual':             'waiting_other',
}

# Convenience set: node types that cause a wait state
WAIT_NODE_TYPES = set(NODE_TYPE_TO_WAIT_TYPE.keys())

# Maps node_type → wait_reason (backwards-compat with old engine)
NODE_TYPE_WAIT_REASONS = {k: WAIT_TYPE_TO_WAIT_REASON[v] for k, v in NODE_TYPE_TO_WAIT_TYPE.items()}


# ---------------------------------------------------------------------------#
# Model 1 – WorkflowInstance                                                  #
# ---------------------------------------------------------------------------#

class WorkflowInstance(BaseModel):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('running',   'Running'),
        ('waiting',   'Waiting'),
        ('paused',    'Paused'),
        ('completed', 'Completed'),
        ('failed',    'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    workflow_id      = models.UUIDField(db_index=True)
    version_id       = models.UUIDField(null=True, blank=True, db_index=True)
    entity_type      = models.CharField(max_length=64, db_index=True)
    entity_id        = models.UUIDField(db_index=True)
    current_stage_id = models.UUIDField(null=True, blank=True, db_index=True)
    status           = models.CharField(max_length=32, choices=STATUS_CHOICES, default='running', db_index=True)
    wait_reason      = models.CharField(max_length=32, choices=WAIT_REASON_CHOICES, null=True, blank=True, db_index=True)
    started_at       = models.DateTimeField(auto_now_add=True)
    completed_at     = models.DateTimeField(null=True, blank=True)
    failed_at        = models.DateTimeField(null=True, blank=True)
    context_data     = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_exec_instances'
        ordering = ['-started_at']


# ---------------------------------------------------------------------------#
# Model 2 – WorkflowStageExecution                                            #
# ---------------------------------------------------------------------------#

class WorkflowStageExecution(BaseModel):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('running',   'Running'),
        ('waiting',   'Waiting'),
        ('completed', 'Completed'),
        ('skipped',   'Skipped'),
        ('failed',    'Failed'),
    ]
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='stage_executions')
    stage_id          = models.UUIDField(db_index=True)
    stage_name        = models.CharField(max_length=255, blank=True)
    status            = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending', db_index=True)
    wait_reason       = models.CharField(max_length=32, choices=WAIT_REASON_CHOICES, null=True, blank=True)
    started_at        = models.DateTimeField(auto_now_add=True)
    completed_at      = models.DateTimeField(null=True, blank=True)
    failed_at         = models.DateTimeField(null=True, blank=True)
    actor_type        = models.CharField(max_length=64, blank=True)
    actor_id          = models.UUIDField(null=True, blank=True)
    metadata          = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_exec_stage_executions'
        ordering = ['started_at']


# ---------------------------------------------------------------------------#
# Model 3 – WorkflowEventTrigger  (legacy raw event log)                      #
# ---------------------------------------------------------------------------#

class WorkflowEventTrigger(BaseModel):
    event_type  = models.CharField(max_length=128, db_index=True)
    entity_type = models.CharField(max_length=64, db_index=True)
    entity_id   = models.UUIDField(db_index=True)
    payload     = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_exec_event_triggers'
        ordering = ['-created_at']


# ---------------------------------------------------------------------------#
# Model 4 – WorkflowExecutionTimeline  (high-level audit)                     #
# ---------------------------------------------------------------------------#

class WorkflowExecutionTimeline(BaseModel):
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='timeline_events')
    stage_id          = models.UUIDField(null=True, blank=True, db_index=True)
    action            = models.CharField(max_length=255)
    actor             = models.CharField(max_length=64, default='system')
    timestamp         = models.DateTimeField(auto_now_add=True)
    metadata          = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_exec_timeline'
        ordering = ['timestamp']


# ---------------------------------------------------------------------------#
# NEW Model 5 – WorkflowStageTransition                                       #
# Defines typed, prioritised transitions for a workflow. Supplements edges.   #
# ---------------------------------------------------------------------------#

class WorkflowStageTransition(BaseModel):
    TRANSITION_TYPES = [
        ('auto',     'Auto'),
        ('decision', 'Decision'),
        ('approval', 'Approval'),
        ('event',    'Event'),
        ('manual',   'Manual'),
        ('wait',     'Wait'),
    ]
    workflow_id      = models.UUIDField(db_index=True)
    from_stage_id    = models.UUIDField(db_index=True)   # WorkflowNode.id
    to_stage_id      = models.UUIDField(db_index=True)   # WorkflowNode.id
    transition_type  = models.CharField(max_length=16, choices=TRANSITION_TYPES, default='auto')
    condition_config = models.JSONField(default=dict, blank=True)
    # condition_config format:
    #   {"operator": "and"|"or", "conditions": [{"field":"score","op":"gt","value":70}, ...]}
    # OR simple single: {"field":"score","op":"gt","value":70}
    priority         = models.IntegerField(default=0)    # lower = higher priority
    label            = models.CharField(max_length=128, blank=True)  # e.g. "pass", "fail", "hold"
    is_active        = models.BooleanField(default=True)

    class Meta:
        db_table = 'wf_exec_stage_transitions'
        ordering = ['priority', 'created_at']


# ---------------------------------------------------------------------------#
# NEW Model 6 – WorkflowWaitState                                             #
# Per-instance explicit wait state with typed reason and resume tracking.     #
# ---------------------------------------------------------------------------#

class WorkflowWaitState(BaseModel):
    WAIT_TYPES = [
        ('approval',           'Approval'),
        ('recruiter_review',   'Recruiter Review'),
        ('candidate_response', 'Candidate Response'),
        ('client_feedback',    'Client Feedback'),
        ('interview_schedule', 'Interview Schedule'),
        ('document_signature', 'Document Signature'),
        ('manual',             'Manual'),
    ]
    STATUS_CHOICES = [
        ('waiting',   'Waiting'),
        ('resumed',   'Resumed'),
        ('expired',   'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='wait_states')
    stage_execution   = models.ForeignKey(WorkflowStageExecution, on_delete=models.SET_NULL, null=True, blank=True, related_name='wait_states')
    wait_type         = models.CharField(max_length=32, default='manual')
    wait_reason       = models.CharField(max_length=255, blank=True)   # human-readable reason
    resume_event      = models.CharField(max_length=128, blank=True)   # event_key that can resume
    timeout_at        = models.DateTimeField(null=True, blank=True)
    status            = models.CharField(max_length=16, choices=STATUS_CHOICES, default='waiting', db_index=True)
    resumed_at        = models.DateTimeField(null=True, blank=True)
    resumed_by        = models.CharField(max_length=64, blank=True)    # 'system'|'user'|'event'
    resume_context    = models.JSONField(default=dict, blank=True)     # payload at resume time

    class Meta:
        db_table = 'wf_exec_wait_states'
        ordering = ['-created_at']

    def do_resume(self, triggered_by='system', context=None):
        self.status     = 'resumed'
        self.resumed_at = timezone.now()
        self.resumed_by = triggered_by
        if context:
            self.resume_context = context
        self.save(update_fields=['status', 'resumed_at', 'resumed_by', 'resume_context', 'updated_at'])


# ---------------------------------------------------------------------------#
# NEW Model 7 – WorkflowTransitionLog                                         #
# Structured per-transition audit (complementary to timeline).                #
# ---------------------------------------------------------------------------#

class WorkflowTransitionLog(BaseModel):
    TRIGGERED_BY_CHOICES = [
        ('system',     'System'),
        ('user',       'User'),
        ('event',      'Event'),
        ('automation', 'Automation'),
    ]
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='transition_logs')
    from_stage        = models.CharField(max_length=128, blank=True)
    to_stage          = models.CharField(max_length=128, blank=True)
    from_stage_id     = models.UUIDField(null=True, blank=True, db_index=True)
    to_stage_id       = models.UUIDField(null=True, blank=True, db_index=True)
    from_stage_name   = models.CharField(max_length=128, blank=True)
    to_stage_name     = models.CharField(max_length=128, blank=True)
    transition_type   = models.CharField(max_length=16, blank=True)
    label             = models.CharField(max_length=128, blank=True)   # e.g. "pass", "fail"
    triggered_by      = models.CharField(max_length=16, choices=TRIGGERED_BY_CHOICES, default='system')
    actor_id          = models.UUIDField(null=True, blank=True)
    reason            = models.TextField(blank=True)
    condition_result  = models.JSONField(default=dict, blank=True)     # what was evaluated

    class Meta:
        db_table = 'wf_exec_transition_logs'
        ordering = ['-created_at']


class WorkflowFailureLog(BaseModel):
    STATUS_CHOICES = [
        ('retrying', 'Retrying'),
        ('failed', 'Failed'),
        ('recovered', 'Recovered'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance, on_delete=models.CASCADE, related_name='failure_logs'
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='failure_logs',
    )
    error_message = models.TextField()
    error_type = models.CharField(max_length=128, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='failed', db_index=True)

    class Meta:
        db_table = 'wf_exec_failure_logs'
        ordering = ['-created_at']


class WorkflowTimeline(BaseModel):
    EVENT_TYPES = [
        ('stage_started', 'Stage Started'),
        ('stage_completed', 'Stage Completed'),
        ('stage_failed', 'Stage Failed'),
        ('transition', 'Transition'),
        ('waiting', 'Waiting'),
        ('resumed', 'Resumed'),
        ('routing', 'Routing'),
        ('actor_changed', 'Actor Changed'),
        ('failure', 'Failure'),
        ('retry', 'Retry'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance, on_delete=models.CASCADE, related_name='unified_timeline'
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timeline_events',
    )
    wait_state = models.ForeignKey(
        WorkflowWaitState,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timeline_events',
    )
    transition_log = models.ForeignKey(
        WorkflowTransitionLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timeline_events',
    )
    failure_log = models.ForeignKey(
        WorkflowFailureLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timeline_events',
    )
    event_type = models.CharField(max_length=32, choices=EVENT_TYPES, db_index=True)
    event_label = models.CharField(max_length=255)
    actor_type = models.CharField(max_length=64, blank=True)
    actor_id = models.UUIDField(null=True, blank=True)
    occurred_at = models.DateTimeField(db_index=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'wf_exec_unified_timeline'
        ordering = ['occurred_at', 'created_at']


class WorkflowExecutionContext(BaseModel):
    SOURCE_TYPES = [
        ('workflow', 'Workflow'),
        ('event', 'Event'),
        ('stage', 'Stage'),
        ('actor', 'Actor'),
        ('routing', 'Routing'),
        ('system', 'System'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance, on_delete=models.CASCADE, related_name='execution_contexts'
    )
    context_key = models.CharField(max_length=128, db_index=True)
    context_value = models.JSONField(default=dict, blank=True)
    source_type = models.CharField(max_length=16, choices=SOURCE_TYPES, default='workflow', db_index=True)

    class Meta:
        db_table = 'wf_exec_contexts'
        ordering = ['-updated_at']


class WorkflowExecutionDecision(BaseModel):
    DECISION_TYPES = [
        ('transition_select', 'Transition Select'),
        ('wait_required', 'Wait Required'),
        ('resume_allowed', 'Resume Allowed'),
        ('routing_required', 'Routing Required'),
        ('retry_required', 'Retry Required'),
        ('completion_check', 'Completion Check'),
        ('failure_classification', 'Failure Classification'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance, on_delete=models.CASCADE, related_name='execution_decisions'
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='execution_decisions',
    )
    decision_type = models.CharField(max_length=32, choices=DECISION_TYPES, db_index=True)
    decision_result = models.CharField(max_length=255)
    decision_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'wf_exec_decisions'
        ordering = ['-created_at']


class WorkflowOrchestratorLog(BaseModel):
    LOG_TYPES = [
        ('start', 'Start'),
        ('stage_enter', 'Stage Enter'),
        ('stage_exit', 'Stage Exit'),
        ('wait', 'Wait'),
        ('resume', 'Resume'),
        ('route', 'Route'),
        ('retry', 'Retry'),
        ('fail', 'Fail'),
        ('complete', 'Complete'),
        ('debug', 'Debug'),
    ]

    workflow_instance = models.ForeignKey(
        WorkflowInstance, on_delete=models.CASCADE, related_name='orchestrator_logs'
    )
    stage_execution = models.ForeignKey(
        WorkflowStageExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orchestrator_logs',
    )
    log_type = models.CharField(max_length=16, choices=LOG_TYPES, db_index=True)
    message = models.TextField()

    class Meta:
        db_table = 'wf_exec_orchestrator_logs'
        ordering = ['-created_at']
