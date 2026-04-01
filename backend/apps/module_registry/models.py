import uuid

from django.db import models

from shared.models import BaseModel


class ModuleStatusChoices(models.TextChoices):
    NOT_STARTED = 'not_started', 'Not Started'
    IN_PROGRESS = 'in_progress', 'In Progress'
    BLOCKED = 'blocked', 'Blocked'
    PARTIAL = 'partial', 'Partial'
    COMPLETE = 'complete', 'Complete'


class ReadinessChoices(models.TextChoices):
    NOT_READY = 'not_ready', 'Not Ready'
    PARTIAL = 'partial', 'Partial'
    READY = 'ready', 'Ready'
    VERIFIED = 'verified', 'Verified'


class PriorityChoices(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'


class BlockerSeverityChoices(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'


class ClassificationChoices(models.TextChoices):
    CRITICAL_NOT_STARTED = 'critical_not_started', 'Critical and Not Started'
    CRITICAL_PARTIAL = 'critical_partial', 'Critical and Partially Built'
    CRITICAL_ARCH_ONLY = 'critical_arch_only', 'Critical and Architecture Only'
    CRITICAL_IMPL_READY = 'critical_impl_ready', 'Critical and Implementation Ready'
    NON_CRITICAL_SOON = 'non_critical_soon', 'Non-Critical but Needed Soon'
    OPTIONAL_LATER = 'optional_later', 'Optional / Later Phase'
    BLOCKED_DEPENDENCY = 'blocked_dependency', 'Blocked by Dependency'
    BLOCKED_BUSINESS_RULE = 'blocked_business_rule', 'Blocked by Business Rule'


class PhaseBucketChoices(models.TextChoices):
    MVP_REQUIRED = 'mvp_required', 'MVP Required'
    PHASE_2_REQUIRED = 'phase_2_required', 'Phase 2 Required'
    ENTERPRISE_EXTENSION = 'enterprise_extension', 'Enterprise Extension'
    FUTURE_INNOVATION = 'future_innovation', 'Future Innovation Layer'


class GapStatusChoices(models.TextChoices):
    NONE = 'none', 'No Gap'
    MINOR = 'minor', 'Minor Gap'
    MODERATE = 'moderate', 'Moderate Gap'
    MAJOR = 'major', 'Major Gap'
    BLOCKING = 'blocking', 'Blocking Gap'


class ModuleRegistry(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module_key = models.CharField(max_length=120, unique=True, db_index=True)
    module_name = models.CharField(max_length=200, db_index=True)
    module_domain = models.CharField(max_length=120, db_index=True)
    status = models.CharField(max_length=20, choices=ModuleStatusChoices.choices, default=ModuleStatusChoices.NOT_STARTED, db_index=True)
    architecture_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    backend_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    frontend_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    integration_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    qa_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    dependency_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    blocker_status = models.CharField(max_length=20, choices=ModuleStatusChoices.choices, default=ModuleStatusChoices.NOT_STARTED, db_index=True)
    priority_level = models.CharField(max_length=20, choices=PriorityChoices.choices, default=PriorityChoices.MEDIUM, db_index=True)
    implementation_order = models.PositiveIntegerField(default=0, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_module_registry'
        ordering = ['implementation_order', 'priority_level', 'module_name']

    def __str__(self):
        return f'{self.module_name} ({self.module_key})'


class ModuleStatus(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.OneToOneField(ModuleRegistry, on_delete=models.CASCADE, related_name='status_record')
    status = models.CharField(max_length=20, choices=ModuleStatusChoices.choices, default=ModuleStatusChoices.NOT_STARTED, db_index=True)
    architecture_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    backend_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    frontend_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    integration_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    qa_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    dependency_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    blocker_status = models.CharField(max_length=20, choices=ModuleStatusChoices.choices, default=ModuleStatusChoices.NOT_STARTED, db_index=True)
    architecture_approved = models.BooleanField(default=False)
    implementation_ready = models.BooleanField(default=False)
    frontend_ready = models.BooleanField(default=False)
    backend_ready = models.BooleanField(default=False)
    verification_required = models.BooleanField(default=True)

    class Meta:
        db_table = 'tos_module_status'

    def __str__(self):
        return f'Status for {self.module.module_key}'


class ModuleDependency(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='dependents')
    dependency_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    is_hard_blocker = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_module_dependency'
        unique_together = [('module', 'depends_on')]

    def __str__(self):
        return f'{self.module.module_key} -> {self.depends_on.module_key}'


class ModuleOwner(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='owners')
    owner_tool = models.CharField(max_length=120, db_index=True)
    owner_name = models.CharField(max_length=200, blank=True)
    responsibility = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_module_owner'

    def __str__(self):
        label = self.owner_name or self.owner_tool
        return f'{self.module.module_key} / {label}'


class ModuleBlocker(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='blockers')
    title = models.CharField(max_length=200)
    blocker_status = models.CharField(max_length=20, choices=ModuleStatusChoices.choices, default=ModuleStatusChoices.BLOCKED, db_index=True)
    priority_level = models.CharField(max_length=20, choices=PriorityChoices.choices, default=PriorityChoices.HIGH, db_index=True)
    severity = models.CharField(max_length=20, choices=BlockerSeverityChoices.choices, default=BlockerSeverityChoices.MEDIUM, db_index=True)
    notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tos_module_blocker'

    def __str__(self):
        return f'{self.module.module_key}: {self.title}'


class ModuleAuditLog(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='audit_logs')
    event_type = models.CharField(max_length=120, db_index=True)
    actor_name = models.CharField(max_length=200, blank=True)
    event_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'tos_module_audit_log'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.module.module_key}: {self.event_type}'


class RemainingModuleMap(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.OneToOneField(ModuleRegistry, on_delete=models.CASCADE, related_name='remaining_map')
    classification_status = models.CharField(
        max_length=40,
        choices=ClassificationChoices.choices,
        default=ClassificationChoices.CRITICAL_NOT_STARTED,
        db_index=True,
    )
    priority_score = models.PositiveIntegerField(default=0, db_index=True)
    mvp_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    enterprise_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    backend_gap_status = models.CharField(max_length=20, choices=GapStatusChoices.choices, default=GapStatusChoices.NONE, db_index=True)
    frontend_gap_status = models.CharField(max_length=20, choices=GapStatusChoices.choices, default=GapStatusChoices.NONE, db_index=True)
    dependency_chain_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    blocker_reason = models.TextField(blank=True)
    recommended_next_action = models.TextField(blank=True)
    phase_bucket = models.CharField(max_length=30, choices=PhaseBucketChoices.choices, default=PhaseBucketChoices.MVP_REQUIRED, db_index=True)
    sequence_order = models.PositiveIntegerField(default=0, db_index=True)
    owner_tool = models.CharField(max_length=120, blank=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_remaining_module_map'
        ordering = ['sequence_order', '-priority_score', 'module__module_name']

    def __str__(self):
        return f'Remaining Map: {self.module.module_key}'


class ModulePriorityRecord(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='priority_records')
    priority_score = models.PositiveIntegerField(default=0, db_index=True)
    product_criticality = models.PositiveIntegerField(default=0)
    dependency_weight = models.PositiveIntegerField(default=0)
    user_journey_impact = models.PositiveIntegerField(default=0)
    frontend_gap_severity = models.PositiveIntegerField(default=0)
    backend_gap_severity = models.PositiveIntegerField(default=0)
    blocker_severity = models.PositiveIntegerField(default=0)
    implementation_readiness = models.PositiveIntegerField(default=0)
    cross_system_impact = models.PositiveIntegerField(default=0)
    near_term_usefulness = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_module_priority_record'
        ordering = ['-priority_score', 'module__module_name']

    def __str__(self):
        return f'Priority: {self.module.module_key} ({self.priority_score})'


class ModuleGapRecord(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='gap_records')
    backend_gap_status = models.CharField(max_length=20, choices=GapStatusChoices.choices, default=GapStatusChoices.NONE, db_index=True)
    frontend_gap_status = models.CharField(max_length=20, choices=GapStatusChoices.choices, default=GapStatusChoices.NONE, db_index=True)
    integration_gap_status = models.CharField(max_length=20, choices=GapStatusChoices.choices, default=GapStatusChoices.NONE, db_index=True)
    architecture_gap_status = models.CharField(max_length=20, choices=GapStatusChoices.choices, default=GapStatusChoices.NONE, db_index=True)
    qa_gap_status = models.CharField(max_length=20, choices=GapStatusChoices.choices, default=GapStatusChoices.NONE, db_index=True)
    blocker_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_module_gap_record'

    def __str__(self):
        return f'Gaps: {self.module.module_key}'


class ModuleClassification(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='classifications')
    classification_status = models.CharField(max_length=40, choices=ClassificationChoices.choices, db_index=True)
    phase_bucket = models.CharField(max_length=30, choices=PhaseBucketChoices.choices, db_index=True)
    is_parallel_safe = models.BooleanField(default=False, db_index=True)
    is_backend_first = models.BooleanField(default=False, db_index=True)
    is_frontend_blocked = models.BooleanField(default=False, db_index=True)
    is_architecture_only = models.BooleanField(default=False, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_module_classification'

    def __str__(self):
        return f'Classification: {self.module.module_key}'


class ModuleSequencePlan(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='sequence_plans')
    sequence_order = models.PositiveIntegerField(default=0, db_index=True)
    phase_bucket = models.CharField(max_length=30, choices=PhaseBucketChoices.choices, default=PhaseBucketChoices.MVP_REQUIRED, db_index=True)
    recommended_next_action = models.TextField(blank=True)
    owner_tool = models.CharField(max_length=120, blank=True, db_index=True)
    is_parallel_safe = models.BooleanField(default=False, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_module_sequence_plan'
        ordering = ['sequence_order', 'module__module_name']

    def __str__(self):
        return f'Sequence: {self.module.module_key} ({self.sequence_order})'


class ModuleDependencyChain(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='dependency_chains')
    depends_on = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='planned_dependents')
    dependency_chain_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    sequence_order = models.PositiveIntegerField(default=0, db_index=True)
    is_hard_dependency = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_module_dependency_chain'
        unique_together = [('module', 'depends_on')]
        ordering = ['sequence_order', 'module__module_name']

    def __str__(self):
        return f'Chain: {self.module.module_key} -> {self.depends_on.module_key}'


class ModuleBuildRecommendation(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='build_recommendations')
    recommended_next_action = models.TextField()
    planning_responsibility = models.CharField(max_length=120, blank=True)
    owner_tool = models.CharField(max_length=120, blank=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_module_build_recommendation'

    def __str__(self):
        return f'Recommendation: {self.module.module_key}'


class ModulePhaseMapping(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='phase_mappings')
    phase_bucket = models.CharField(max_length=30, choices=PhaseBucketChoices.choices, db_index=True)
    mvp_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    enterprise_status = models.CharField(max_length=20, choices=ReadinessChoices.choices, default=ReadinessChoices.NOT_READY, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_module_phase_mapping'

    def __str__(self):
        return f'Phase: {self.module.module_key} / {self.phase_bucket}'


class ModuleContinuationNote(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='continuation_notes')
    note = models.TextField()
    owner_tool = models.CharField(max_length=120, blank=True, db_index=True)
    next_prompt_hint = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'tos_module_continuation_note'
        ordering = ['-created_at']

    def __str__(self):
        return f'Continuation: {self.module.module_key}'


class ModulePlanningAuditLog(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='planning_audit_logs')
    event_type = models.CharField(max_length=120, db_index=True)
    actor_name = models.CharField(max_length=200, blank=True)
    event_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'tos_module_planning_audit_log'
        ordering = ['-created_at']

    def __str__(self):
        return f'Planning Audit: {self.module.module_key} / {self.event_type}'


class SelectionStatusChoices(models.TextChoices):
    CANDIDATE = 'candidate', 'Candidate'
    SELECTED = 'selected', 'Selected'
    REJECTED = 'rejected', 'Rejected'
    BLOCKED = 'blocked', 'Blocked'
    LOCKED = 'locked', 'Locked'


class BuildModeChoices(models.TextChoices):
    BACKEND_FIRST = 'backend_first', 'Backend First'
    FRONTEND_FIRST = 'frontend_first', 'Frontend First'
    FULL_STACK = 'full_stack', 'Full Stack'
    SPLIT_FIRST = 'split_first', 'Split First'
    DEFER = 'defer', 'Defer'


class CandidateStatusChoices(models.TextChoices):
    IMMEDIATE = 'immediate', 'Immediate Build Candidate'
    HOLD = 'hold', 'Hold'
    BLOCKED = 'blocked', 'Blocked'
    DEFERRED = 'deferred', 'Deferred'


class NextModuleSelection(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='next_module_selections')
    candidate_status = models.CharField(max_length=20, choices=CandidateStatusChoices.choices, default=CandidateStatusChoices.IMMEDIATE, db_index=True)
    criticality_score = models.PositiveIntegerField(default=0)
    dependency_score = models.PositiveIntegerField(default=0)
    journey_impact_score = models.PositiveIntegerField(default=0)
    frontend_gap_score = models.PositiveIntegerField(default=0)
    backend_gap_score = models.PositiveIntegerField(default=0)
    readiness_score = models.PositiveIntegerField(default=0)
    ambiguity_score = models.PositiveIntegerField(default=0)
    delay_risk_score = models.PositiveIntegerField(default=0)
    final_selection_score = models.PositiveIntegerField(default=0, db_index=True)
    selection_status = models.CharField(max_length=20, choices=SelectionStatusChoices.choices, default=SelectionStatusChoices.CANDIDATE, db_index=True)
    rejection_reason = models.TextField(blank=True)
    recommended_build_mode = models.CharField(max_length=20, choices=BuildModeChoices.choices, default=BuildModeChoices.BACKEND_FIRST, db_index=True)
    recommended_owner_type = models.CharField(max_length=120, blank=True)
    recommended_next_step = models.TextField(blank=True)
    sequence_rank = models.PositiveIntegerField(default=0, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_next_module_selection'
        ordering = ['-final_selection_score', 'sequence_rank', 'module__module_name']

    def __str__(self):
        return f'Next Selection: {self.module.module_key}'


class NextModuleCandidateScore(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='next_candidate_scores')
    candidate_status = models.CharField(max_length=20, choices=CandidateStatusChoices.choices, default=CandidateStatusChoices.IMMEDIATE, db_index=True)
    criticality_score = models.PositiveIntegerField(default=0)
    dependency_score = models.PositiveIntegerField(default=0)
    journey_impact_score = models.PositiveIntegerField(default=0)
    frontend_gap_score = models.PositiveIntegerField(default=0)
    backend_gap_score = models.PositiveIntegerField(default=0)
    readiness_score = models.PositiveIntegerField(default=0)
    ambiguity_score = models.PositiveIntegerField(default=0)
    final_selection_score = models.PositiveIntegerField(default=0, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_next_module_candidate_score'
        ordering = ['-final_selection_score', 'module__module_name']

    def __str__(self):
        return f'Candidate Score: {self.module.module_key}'


class NextModuleDependencyPressure(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='next_dependency_pressures')
    dependency_score = models.PositiveIntegerField(default=0)
    blocking_dependency_count = models.PositiveIntegerField(default=0)
    downstream_modules_affected = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_next_module_dependency_pressure'
        ordering = ['-dependency_score', 'module__module_name']

    def __str__(self):
        return f'Dependency Pressure: {self.module.module_key}'


class NextModuleDelayRisk(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='next_delay_risks')
    delay_risk_score = models.PositiveIntegerField(default=0, db_index=True)
    user_journey_risk = models.PositiveIntegerField(default=0)
    dependency_risk = models.PositiveIntegerField(default=0)
    coordination_risk = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_next_module_delay_risk'
        ordering = ['-delay_risk_score', 'module__module_name']

    def __str__(self):
        return f'Delay Risk: {self.module.module_key}'


class NextModuleReadinessRecord(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='next_readiness_records')
    readiness_score = models.PositiveIntegerField(default=0, db_index=True)
    ambiguity_score = models.PositiveIntegerField(default=0)
    backend_first_recommended = models.BooleanField(default=True, db_index=True)
    frontend_first_recommended = models.BooleanField(default=False, db_index=True)
    blocked_by_business_rule = models.BooleanField(default=False, db_index=True)
    can_codex_start_immediately = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_next_module_readiness_record'

    def __str__(self):
        return f'Readiness: {self.module.module_key}'


class NextModuleRecommendation(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='next_recommendations')
    selection_status = models.CharField(max_length=20, choices=SelectionStatusChoices.choices, default=SelectionStatusChoices.SELECTED, db_index=True)
    recommended_build_mode = models.CharField(max_length=20, choices=BuildModeChoices.choices, default=BuildModeChoices.BACKEND_FIRST, db_index=True)
    recommended_owner_type = models.CharField(max_length=120, blank=True)
    recommended_next_step = models.TextField(blank=True)
    why_selected = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_next_module_recommendation'

    def __str__(self):
        return f'Recommendation: {self.module.module_key}'


class NextModuleRejectionReason(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='next_rejection_reasons')
    rejection_reason = models.TextField()
    rejected_due_to = models.CharField(max_length=120, blank=True)
    sequence_rank = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        db_table = 'tos_next_module_rejection_reason'
        ordering = ['sequence_rank', 'module__module_name']

    def __str__(self):
        return f'Rejection: {self.module.module_key}'


class NextModuleSequencePlan(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='next_sequence_plans')
    sequence_rank = models.PositiveIntegerField(default=0, db_index=True)
    recommended_next_step = models.TextField(blank=True)
    recommended_build_mode = models.CharField(max_length=20, choices=BuildModeChoices.choices, default=BuildModeChoices.BACKEND_FIRST, db_index=True)
    prerequisite_summary = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_next_module_sequence_plan'
        ordering = ['sequence_rank', 'module__module_name']

    def __str__(self):
        return f'Next Sequence: {self.module.module_key}'


class NextModuleDecisionAudit(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='next_decision_audits')
    event_type = models.CharField(max_length=120, db_index=True)
    actor_name = models.CharField(max_length=200, blank=True)
    event_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'tos_next_module_decision_audit'
        ordering = ['-created_at']

    def __str__(self):
        return f'Next Decision Audit: {self.module.module_key} / {self.event_type}'


class PromptStatusChoices(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    GENERATED = 'generated', 'Generated'
    APPROVED = 'approved', 'Approved'
    LOCKED = 'locked', 'Locked'


class GeneratedPrompt(BaseModel):
    prompt_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    module = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='generated_prompts')
    prompt_title = models.CharField(max_length=255, db_index=True)
    prompt_scope = models.TextField()
    prompt_dependencies = models.JSONField(default=list, blank=True)
    prompt_status = models.CharField(max_length=20, choices=PromptStatusChoices.choices, default=PromptStatusChoices.DRAFT, db_index=True)
    prompt_version = models.PositiveIntegerField(default=1, db_index=True)
    generated_by = models.CharField(max_length=120, blank=True)
    approved_by = models.CharField(max_length=120, blank=True)
    prompt_body = models.TextField()

    class Meta:
        db_table = 'tos_generated_prompt'
        ordering = ['-created_at']

    def __str__(self):
        return f'Prompt: {self.module.module_key} v{self.prompt_version}'


class PromptContext(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt = models.ForeignKey(GeneratedPrompt, on_delete=models.CASCADE, related_name='contexts')
    module_key = models.CharField(max_length=120, db_index=True)
    context_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'tos_prompt_context'

    def __str__(self):
        return f'Prompt Context: {self.module_key}'


class PromptDependency(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt = models.ForeignKey(GeneratedPrompt, on_delete=models.CASCADE, related_name='dependencies_map')
    depends_on = models.ForeignKey(ModuleRegistry, on_delete=models.CASCADE, related_name='prompt_dependents')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tos_prompt_dependency'

    def __str__(self):
        return f'Prompt Dependency: {self.prompt.module.module_key} -> {self.depends_on.module_key}'


class PromptScope(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt = models.ForeignKey(GeneratedPrompt, on_delete=models.CASCADE, related_name='scopes')
    scope_type = models.CharField(max_length=120, db_index=True)
    scope_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'tos_prompt_scope'

    def __str__(self):
        return f'Prompt Scope: {self.scope_type}'


class PromptHistory(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt = models.ForeignKey(GeneratedPrompt, on_delete=models.CASCADE, related_name='history')
    event_type = models.CharField(max_length=120, db_index=True)
    actor_name = models.CharField(max_length=200, blank=True)
    event_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'tos_prompt_history'
        ordering = ['-created_at']

    def __str__(self):
        return f'Prompt History: {self.prompt.module.module_key} / {self.event_type}'


class PromptVersion(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt = models.ForeignKey(GeneratedPrompt, on_delete=models.CASCADE, related_name='versions')
    prompt_version = models.PositiveIntegerField(default=1, db_index=True)
    version_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'tos_prompt_version'
        ordering = ['-prompt_version']

    def __str__(self):
        return f'Prompt Version: {self.prompt.module.module_key} v{self.prompt_version}'
