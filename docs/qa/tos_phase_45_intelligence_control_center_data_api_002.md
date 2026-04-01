# TOS-ICC-DATA-API-002

## 1. Django App Structure

Product label:
- `Intelligence Control Center`

Locked internal backend app name:
- `apps/orchestration_center`

Reason:
- `ICC` is already used in TOS for `Interview Command Center`
- use the product label in UI and docs, but keep the Django/app namespace collision-free

Recommended structure:

```text
apps/orchestration_center/
  __init__.py
  admin.py
  apps.py
  constants/
    actions.py
    approvals.py
    connectors.py
    execution_statuses.py
    failure_codes.py
    prompt_statuses.py
    provider_statuses.py
    rule_statuses.py
  models/
    __init__.py
    provider.py
    prompt.py
    ai_execution.py
    automation.py
    governance.py
    connector.py
    audit.py
  selectors/
    overview.py
    providers.py
    prompts.py
    executions.py
    automations.py
    failures.py
    approvals.py
  services/
    provider_router.py
    prompt_registry_service.py
    ai_execution_service.py
    automation_rule_service.py
    approval_service.py
    failure_service.py
    connector_service.py
    tenant_settings_service.py
    audit_service.py
  policies/
    routing_policy.py
    approval_policy.py
    tenant_policy.py
    rule_policy.py
  consumers/
    event_consumers.py
  tasks/
    ai_tasks.py
    automation_tasks.py
    retry_tasks.py
    health_tasks.py
    metrics_tasks.py
  api/
    serializers/
      overview.py
      providers.py
      prompts.py
      executions.py
      automations.py
      failures.py
      approvals.py
      settings.py
    views/
      overview.py
      providers.py
      prompts.py
      executions.py
      automations.py
      failures.py
      approvals.py
      settings.py
    urls.py
    permissions.py
  utils/
    idempotency.py
    schema_validation.py
    payload_ref.py
    locking.py
  migrations/
```

Responsibilities:
- `models/`: normalized persistence and history
- `services/`: write-side orchestration rules
- `selectors/`: read-side queries and dashboard aggregation
- `consumers/`: event-to-execution registration
- `tasks/`: async execution
- `policies/`: tenant, approval, and routing constraints
- `api/`: contract layer only, no orchestration logic

## 2. Model Set And Relationships

### Platform configuration tables
- `ai_providers`
- `ai_models`
- `provider_configs`
- `model_routing_rules`
- `intelligence_connectors`

### Prompt registry tables
- `prompt_templates`
- `prompt_versions`
- `prompt_scopes`
- `prompt_test_runs`

### AI execution tables
- `ai_execution_requests`
- `ai_execution_results`
- `ai_execution_artifacts`
- `ai_execution_reviews`

### Automation engine tables
- `automation_rules`
- `automation_rule_conditions`
- `automation_rule_actions`
- `automation_rule_scopes`
- `automation_execution_runs`
- `automation_scheduled_actions`

### Governance / operations tables
- `tenant_intelligence_settings`
- `execution_failures`
- `dead_letter_items`
- `approval_queue_items`
- `intelligence_audit_logs`

Relationship summary:
- one provider has many models
- one model may have many routing rules
- one prompt template has many versions and scopes
- one AI execution request has one result, many artifacts, and zero or one review
- one automation rule has many conditions, actions, scopes, and execution runs
- one failure may reference one AI request or one automation run
- one approval queue item references one originating object

## 3. Field-Level Model Design

### A. Provider / Model Layer

### `ai_providers`
Purpose:
- register available providers, local runtimes, or external vendors

Tenant awareness:
- platform-wide by default
- tenant override optional through `tenant_id nullable`

Fields:
- `id: UUIDField`
- `tenant_id: ForeignKey(Tenant, null=True, blank=True)`
- `provider_key: CharField(64)`
- `provider_name: CharField(128)`
- `provider_type: CharField(32)`  
  values: `local`, `external_api`, `internal_service`
- `status: CharField(32)`  
  values: `active`, `inactive`, `degraded`, `disabled`, `deprecated`
- `base_url: URLField(null=True, blank=True)`
- `api_version: CharField(32, blank=True)`
- `timeout_seconds: PositiveIntegerField(default=30)`
- `connect_timeout_seconds: PositiveIntegerField(default=5)`
- `read_timeout_seconds: PositiveIntegerField(default=25)`
- `max_retries: PositiveSmallIntegerField(default=2)`
- `priority_order: PositiveSmallIntegerField(default=100)`
- `supports_streaming: BooleanField(default=False)`
- `supports_structured_output: BooleanField(default=False)`
- `health_status: CharField(32)`  
  values: `unknown`, `healthy`, `warning`, `unhealthy`
- `last_health_checked_at: DateTimeField(null=True, blank=True)`
- `metadata_json: JSONField(default=dict, blank=True)`
- `is_deleted: BooleanField(default=False)`
- audit fields

Indexes:
- `(tenant_id, provider_key)`
- `(status, priority_order)`
- `(health_status, last_health_checked_at)`

Uniqueness:
- unique `(tenant_id, provider_key)` where soft-deleted = false

### `ai_models`
Purpose:
- list models available under a provider

Fields:
- `id: UUIDField`
- `provider: ForeignKey(ai_providers)`
- `tenant_id: ForeignKey(Tenant, null=True, blank=True)`
- `model_key: CharField(128)`
- `model_name: CharField(128)`
- `capability_type: CharField(64)`  
  examples: `resume_parse`, `ranking`, `drafting`, `summarization`, `classification`, `general`
- `status: CharField(32)`  
  values: `active`, `inactive`, `deprecated`, `disabled`
- `context_window: IntegerField(null=True, blank=True)`
- `max_output_tokens: IntegerField(null=True, blank=True)`
- `cost_class: CharField(32, blank=True)`
- `supports_json_schema: BooleanField(default=False)`
- `supports_tools: BooleanField(default=False)`
- `supports_multimodal: BooleanField(default=False)`
- `latency_tier: CharField(32, blank=True)`
- `quality_tier: CharField(32, blank=True)`
- `health_status: CharField(32, default='unknown')`
- `metadata_json: JSONField(default=dict, blank=True)`
- `is_deleted: BooleanField(default=False)`
- audit fields

Indexes:
- `(provider_id, status)`
- `(tenant_id, capability_type, status)`
- `(health_status, status)`

Uniqueness:
- unique `(provider_id, tenant_id, model_key)` where soft-deleted = false

### `provider_configs`
Purpose:
- store environment-aware provider configuration references

Fields:
- `id`
- `provider: ForeignKey(ai_providers)`
- `environment: CharField(32)`  
  values: `dev`, `staging`, `prod`
- `credential_ref: CharField(255)`
- `allowed_use_cases_json: JSONField(default=list, blank=True)`
- `rate_limit_per_minute: IntegerField(null=True, blank=True)`
- `cost_limit_daily: DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)`
- `is_active: BooleanField(default=True)`
- audit fields

Indexes:
- `(provider_id, environment, is_active)`

### `model_routing_rules`
Purpose:
- resolve which provider/model to use per feature and tenant

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant, null=True, blank=True)`
- `module_scope: CharField(64)`  
  examples: `candidates`, `pipeline`, `interviews`, `communication`, `hdc`
- `use_case_key: CharField(64)`  
  examples: `resume_parsing`, `candidate_ranking`, `interview_summary`, `email_draft`
- `primary_provider: ForeignKey(ai_providers)`
- `primary_model: ForeignKey(ai_models)`
- `fallback_chain_json: JSONField(default=list, blank=True)`  
  list of provider/model refs
- `timeout_override_seconds: IntegerField(null=True, blank=True)`
- `retry_override_count: PositiveSmallIntegerField(null=True, blank=True)`
- `approval_mode: CharField(32)`  
  values: `suggestion_only`, `auto_apply`, `approval_required`
- `status: CharField(32)`  
  values: `active`, `inactive`, `testing`
- audit fields

Indexes:
- `(tenant_id, module_scope, use_case_key, status)`

Uniqueness:
- unique `(tenant_id, module_scope, use_case_key)` where status != archived

### B. Prompt Registry

### `prompt_templates`
Purpose:
- stable named prompt definitions for a module and use case

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant, null=True, blank=True)`
- `prompt_key: CharField(128)`
- `prompt_title: CharField(255)`
- `module_scope: CharField(64)`
- `use_case_key: CharField(64)`
- `description: TextField(blank=True)`
- `status: CharField(32)`  
  values: `draft`, `approved`, `active`, `archived`
- `active_version_id: UUIDField(null=True, blank=True)`
- `approval_required: BooleanField(default=True)`
- `tenant_override_allowed: BooleanField(default=False)`
- `safety_notes: TextField(blank=True)`
- `owner_role: CharField(64, blank=True)`
- `is_deleted: BooleanField(default=False)`
- audit fields

Indexes:
- `(tenant_id, module_scope, use_case_key, status)`
- `(prompt_key, status)`

Uniqueness:
- unique `(tenant_id, prompt_key)` where soft-deleted = false

### `prompt_versions`
Purpose:
- versioned prompt payloads and schemas

Fields:
- `id`
- `prompt_template: ForeignKey(prompt_templates)`
- `version_number: PositiveIntegerField()`
- `status: CharField(32)`  
  values: `draft`, `pending_approval`, `approved`, `active`, `rejected`, `archived`
- `system_prompt: TextField()`
- `user_prompt_template: TextField()`
- `variables_schema_json: JSONField(default=dict)`
- `expected_output_schema_json: JSONField(default=dict)`
- `validation_rules_json: JSONField(default=dict)`
- `fallback_version_id: UUIDField(null=True, blank=True)`
- `approval_required: BooleanField(default=True)`
- `approved_by_id: UUIDField(null=True, blank=True)`
- `approved_at: DateTimeField(null=True, blank=True)`
- `activation_notes: TextField(blank=True)`
- `diff_notes: TextField(blank=True)`
- audit fields

Indexes:
- `(prompt_template_id, version_number desc)`
- `(status, approved_at)`

Uniqueness:
- unique `(prompt_template_id, version_number)`

### `prompt_scopes`
Purpose:
- bind prompt templates to precise entity/use-case/tenant scopes

Fields:
- `id`
- `prompt_template: ForeignKey(prompt_templates)`
- `tenant_id: ForeignKey(Tenant, null=True, blank=True)`
- `module_scope: CharField(64)`
- `entity_type: CharField(64)`
- `use_case_key: CharField(64)`
- `priority_order: PositiveSmallIntegerField(default=100)`
- `is_active: BooleanField(default=True)`
- audit fields

Indexes:
- `(tenant_id, module_scope, use_case_key, is_active, priority_order)`

### `prompt_test_runs`
Purpose:
- capture test console executions before activation

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant, null=True, blank=True)`
- `prompt_version: ForeignKey(prompt_versions)`
- `test_input_json: JSONField(default=dict)`
- `raw_response_ref: CharField(255, blank=True)`
- `normalized_output_json: JSONField(default=dict)`
- `validation_status: CharField(32)`  
  values: `passed`, `failed`, `partial`
- `run_status: CharField(32)`  
  values: `queued`, `running`, `completed`, `failed`
- `executed_by_id: UUIDField(null=True, blank=True)`
- `notes: TextField(blank=True)`
- audit fields

Indexes:
- `(prompt_version_id, created_at desc)`
- `(tenant_id, validation_status)`

### C. AI Execution Layer

### `ai_execution_requests`
Purpose:
- immutable request record for an AI execution attempt

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant)`
- `module_scope: CharField(64)`
- `use_case_key: CharField(64)`
- `source_event: CharField(128, blank=True)`
- `source_entity_type: CharField(64)`
- `source_entity_id: CharField(64)`
- `source_module: CharField(64)`
- `prompt_version: ForeignKey(prompt_versions)`
- `provider: ForeignKey(ai_providers, null=True, blank=True)`
- `model: ForeignKey(ai_models, null=True, blank=True)`
- `mode: CharField(32)`  
  values: `suggestion_only`, `auto_apply`, `approval_required`
- `status: CharField(32)`  
  values: `queued`, `running`, `completed`, `failed`, `partial`, `requires_review`, `cancelled`
- `context_snapshot_json: JSONField(default=dict)`
- `idempotency_key: CharField(255, blank=True)`
- `retry_count: PositiveSmallIntegerField(default=0)`
- `max_retries: PositiveSmallIntegerField(default=2)`
- `queued_at: DateTimeField(auto_now_add=True)`
- `started_at: DateTimeField(null=True, blank=True)`
- `completed_at: DateTimeField(null=True, blank=True)`
- `cancelled_at: DateTimeField(null=True, blank=True)`
- `failure_category: CharField(64, blank=True)`
- `failure_reason: TextField(blank=True)`
- `requires_review: BooleanField(default=False)`
- `requires_approval: BooleanField(default=False)`
- `final_disposition: CharField(32, blank=True)`  
  values: `suggested`, `applied`, `rejected`, `ignored`, `failed`
- audit fields

Indexes:
- `(tenant_id, status, queued_at)`
- `(source_entity_type, source_entity_id, created_at desc)`
- `(module_scope, use_case_key, status)`
- unique `(idempotency_key)` where idempotency_key != ''

### `ai_execution_results`
Purpose:
- store outcome payload and normalized result

Fields:
- `id`
- `request: OneToOneField(ai_execution_requests)`
- `raw_response_ref: CharField(255, blank=True)`
- `normalized_output_json: JSONField(default=dict)`
- `validation_status: CharField(32)`  
  values: `valid`, `invalid`, `partial`, `not_checked`
- `confidence_score: DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)`
- `token_input_count: IntegerField(null=True, blank=True)`
- `token_output_count: IntegerField(null=True, blank=True)`
- `estimated_cost: DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)`
- `execution_ms: IntegerField(null=True, blank=True)`
- `schema_errors_json: JSONField(default=list, blank=True)`
- `warnings_json: JSONField(default=list, blank=True)`
- audit fields

Indexes:
- `(validation_status, created_at)`

### `ai_execution_artifacts`
Purpose:
- attach generated artifacts such as draft text, parsed structures, summaries

Fields:
- `id`
- `request: ForeignKey(ai_execution_requests)`
- `artifact_type: CharField(64)`  
  examples: `draft_email`, `resume_structured`, `summary_text`, `scorecard_json`
- `storage_ref: CharField(255)`
- `content_hash: CharField(128, blank=True)`
- `metadata_json: JSONField(default=dict, blank=True)`
- audit fields

Indexes:
- `(request_id, artifact_type)`

### `ai_execution_reviews`
Purpose:
- human review / approval / rejection for outputs

Fields:
- `id`
- `request: OneToOneField(ai_execution_requests)`
- `review_status: CharField(32)`  
  values: `pending`, `approved`, `rejected`, `returned`, `not_required`
- `reviewed_by_id: UUIDField(null=True, blank=True)`
- `reviewed_at: DateTimeField(null=True, blank=True)`
- `decision_comment: TextField(blank=True)`
- `applied_by_id: UUIDField(null=True, blank=True)`
- `applied_at: DateTimeField(null=True, blank=True)`
- `application_status: CharField(32)`  
  values: `pending`, `applied`, `not_applied`
- audit fields

Indexes:
- `(review_status, reviewed_at)`

### D. Automation Layer

### `automation_rules`
Purpose:
- define executable automation rules

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant, null=True, blank=True)`
- `rule_key: CharField(128)`
- `rule_title: CharField(255)`
- `module_scope: CharField(64)`
- `trigger_event: CharField(128)`
- `mode: CharField(32)`  
  values: `suggestion_only`, `auto_execute`, `approval_required`
- `status: CharField(32)`  
  values: `draft`, `active`, `inactive`, `paused`, `archived`, `testing`
- `is_builtin: BooleanField(default=False)`
- `dry_run_enabled: BooleanField(default=False)`
- `requires_high_risk_approval: BooleanField(default=False)`
- `max_executions_per_day: IntegerField(null=True, blank=True)`
- `duplicate_window_seconds: IntegerField(default=300)`
- `priority_order: PositiveSmallIntegerField(default=100)`
- `notes: TextField(blank=True)`
- `is_deleted: BooleanField(default=False)`
- audit fields

Indexes:
- `(tenant_id, module_scope, status)`
- `(trigger_event, status, priority_order)`
- `(rule_key, tenant_id)`

Uniqueness:
- unique `(tenant_id, rule_key)` where soft-deleted = false

### `automation_rule_conditions`
Purpose:
- represent IF conditions

Fields:
- `id`
- `rule: ForeignKey(automation_rules)`
- `condition_group: CharField(32, default='default')`
- `field_path: CharField(255)`
- `operator: CharField(32)`  
  examples: `eq`, `neq`, `gt`, `lt`, `in`, `not_in`, `contains`, `elapsed_gt`, `feature_enabled`
- `expected_value_json: JSONField(default=dict)`
- `sequence_order: PositiveSmallIntegerField(default=1)`
- `is_negated: BooleanField(default=False)`
- audit fields

Indexes:
- `(rule_id, condition_group, sequence_order)`

### `automation_rule_actions`
Purpose:
- represent THEN actions

Fields:
- `id`
- `rule: ForeignKey(automation_rules)`
- `action_type: CharField(64)`  
  examples: `notify`, `create_deadline`, `escalate`, `assign`, `schedule_followup`, `invoke_ai`, `create_review_task`, `mark_flag`, `enqueue_communication`, `trigger_webhook`
- `action_config_json: JSONField(default=dict)`
- `delay_seconds: IntegerField(default=0)`
- `requires_approval: BooleanField(default=False)`
- `sequence_order: PositiveSmallIntegerField(default=1)`
- audit fields

Indexes:
- `(rule_id, sequence_order)`

### `automation_rule_scopes`
Purpose:
- define where a rule is allowed to run

Fields:
- `id`
- `rule: ForeignKey(automation_rules)`
- `tenant_id: ForeignKey(Tenant, null=True, blank=True)`
- `entity_type: CharField(64, blank=True)`
- `stage_key: CharField(64, blank=True)`
- `role_scope: CharField(64, blank=True)`
- `source_scope: CharField(64, blank=True)`
- `working_hours_only: BooleanField(default=False)`
- `is_active: BooleanField(default=True)`
- audit fields

Indexes:
- `(rule_id, tenant_id, is_active)`

### `automation_execution_runs`
Purpose:
- execution record for one rule run

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant)`
- `rule: ForeignKey(automation_rules)`
- `source_event: CharField(128)`
- `source_module: CharField(64)`
- `source_entity_type: CharField(64)`
- `source_entity_id: CharField(64)`
- `status: CharField(32)`  
  values: `queued`, `scheduled`, `running`, `completed`, `failed`, `partial`, `cancelled`, `requires_review`
- `mode: CharField(32)`  
  values: `suggestion_only`, `auto_execute`, `approval_required`
- `dedupe_key: CharField(255, blank=True)`
- `trigger_payload_json: JSONField(default=dict)`
- `evaluated_conditions_json: JSONField(default=list)`
- `action_results_json: JSONField(default=list)`
- `scheduled_for: DateTimeField(null=True, blank=True)`
- `started_at: DateTimeField(null=True, blank=True)`
- `completed_at: DateTimeField(null=True, blank=True)`
- `retry_count: PositiveSmallIntegerField(default=0)`
- `failure_category: CharField(64, blank=True)`
- `failure_reason: TextField(blank=True)`
- audit fields

Indexes:
- `(tenant_id, status, scheduled_for)`
- `(rule_id, created_at desc)`
- `(source_entity_type, source_entity_id)`
- unique `(dedupe_key)` where dedupe_key != ''

### `automation_scheduled_actions`
Purpose:
- delayed or recurring action queue

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant)`
- `run: ForeignKey(automation_execution_runs)`
- `action_type: CharField(64)`
- `status: CharField(32)`  
  values: `pending`, `dispatched`, `completed`, `cancelled`, `failed`
- `execute_at: DateTimeField()`
- `attempt_count: PositiveSmallIntegerField(default=0)`
- `payload_json: JSONField(default=dict)`
- `last_error: TextField(blank=True)`
- audit fields

Indexes:
- `(tenant_id, status, execute_at)`
- `(run_id, status)`

### E. Governance / Operations

### `intelligence_connectors`
Purpose:
- declare module integration contracts to ICC

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant, null=True, blank=True)`
- `module_code: CharField(64)`  
  examples: `jobs`, `candidates`, `pipeline`, `interviews`, `communication`, `passport`, `analytics`
- `status: CharField(32)`  
  values: `active`, `inactive`, `disabled`, `testing`
- `events_consumed_json: JSONField(default=list)`
- `ai_actions_allowed_json: JSONField(default=list)`
- `automation_actions_allowed_json: JSONField(default=list)`
- `fallback_behavior: CharField(64)`  
  values: `manual_continue`, `warn_only`, `skip_execution`
- `compatibility_notes: TextField(blank=True)`
- `version_tag: CharField(64, blank=True)`
- audit fields

Indexes:
- `(tenant_id, module_code, status)`

Uniqueness:
- unique `(tenant_id, module_code)`

### `tenant_intelligence_settings`
Purpose:
- tenant-wide feature toggles and policies

Fields:
- `id`
- `tenant_id: OneToOneField(Tenant)`
- `ai_enabled: BooleanField(default=False)`
- `automation_enabled: BooleanField(default=False)`
- `default_approval_mode: CharField(32, default='suggestion_only')`
- `allowed_provider_ids_json: JSONField(default=list)`
- `feature_flags_json: JSONField(default=dict)`
- `notification_preferences_json: JSONField(default=dict)`
- `retry_policy_overrides_json: JSONField(default=dict)`
- `connector_enablement_json: JSONField(default=dict)`
- `visibility_permissions_json: JSONField(default=dict)`
- `updated_by_id: UUIDField(null=True, blank=True)`
- audit fields

Indexes:
- unique `(tenant_id)`

### `execution_failures`
Purpose:
- operator-visible failure tracker

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant)`
- `failure_type: CharField(32)`  
  values: `ai_execution`, `automation_execution`, `prompt_test`, `provider_health`
- `related_request_id: UUIDField(null=True, blank=True)`
- `related_run_id: UUIDField(null=True, blank=True)`
- `category: CharField(64)`  
  values: `provider_timeout`, `invalid_response`, `validation_failure`, `connector_disabled`, `permission_denied`, `rule_misconfiguration`, `missing_dependency`, `system_exception`, `tenant_setting_disabled`
- `severity: CharField(32)`  
  values: `low`, `medium`, `high`, `critical`
- `status: CharField(32)`  
  values: `new`, `triaged`, `retrying`, `resolved`, `moved_to_dead_letter`, `ignored`
- `retryable: BooleanField(default=True)`
- `max_retries: PositiveSmallIntegerField(default=2)`
- `next_retry_at: DateTimeField(null=True, blank=True)`
- `operator_notes: TextField(blank=True)`
- `last_error_message: TextField(blank=True)`
- `resolved_by_id: UUIDField(null=True, blank=True)`
- `resolved_at: DateTimeField(null=True, blank=True)`
- audit fields

Indexes:
- `(tenant_id, status, severity)`
- `(retryable, next_retry_at)`
- `(category, status)`

### `dead_letter_items`
Purpose:
- terminal failures after retry exhaustion or manual parking

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant)`
- `item_type: CharField(32)`  
  values: `ai_execution`, `automation_execution`, `scheduled_action`
- `related_object_id: UUIDField()`
- `reason_code: CharField(64)`
- `payload_snapshot_json: JSONField(default=dict)`
- `status: CharField(32)`  
  values: `open`, `requeued`, `resolved`, `ignored`
- `requeue_count: PositiveSmallIntegerField(default=0)`
- `resolved_by_id: UUIDField(null=True, blank=True)`
- `resolved_at: DateTimeField(null=True, blank=True)`
- `notes: TextField(blank=True)`
- audit fields

Indexes:
- `(tenant_id, status, created_at)`

### `approval_queue_items`
Purpose:
- unified approval queue for AI and automation

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant)`
- `item_type: CharField(64)`  
  values: `ai_output`, `automation_action`, `prompt_activation`, `rule_activation`, `rerun_request`
- `origin_type: CharField(32)`  
  values: `ai_request`, `automation_run`, `prompt_version`, `automation_rule`
- `origin_id: UUIDField()`
- `requested_action: CharField(64)`
- `summary_payload_json: JSONField(default=dict)`
- `recommended_decision: CharField(32, blank=True)`  
  values: `approve`, `reject`, `review`
- `approver_role: CharField(64)`
- `status: CharField(32)`  
  values: `pending`, `approved`, `rejected`, `expired`, `cancelled`
- `decision_comment: TextField(blank=True)`
- `decided_by_id: UUIDField(null=True, blank=True)`
- `decided_at: DateTimeField(null=True, blank=True)`
- `applied_by_id: UUIDField(null=True, blank=True)`
- `applied_at: DateTimeField(null=True, blank=True)`
- audit fields

Indexes:
- `(tenant_id, status, approver_role)`
- `(origin_type, origin_id)`

### `intelligence_audit_logs`
Purpose:
- immutable audit trail for config changes, approvals, reruns, toggles, and operations

Fields:
- `id`
- `tenant_id: ForeignKey(Tenant, null=True, blank=True)`
- `actor_id: UUIDField(null=True, blank=True)`
- `actor_type: CharField(32)`  
  values: `user`, `system`, `worker`
- `action_type: CharField(64)`
- `target_type: CharField(64)`
- `target_id: UUIDField(null=True, blank=True)`
- `before_state_json: JSONField(default=dict, blank=True)`
- `after_state_json: JSONField(default=dict, blank=True)`
- `metadata_json: JSONField(default=dict, blank=True)`
- `created_at: DateTimeField(auto_now_add=True)`

Indexes:
- `(tenant_id, action_type, created_at desc)`
- `(target_type, target_id, created_at desc)`

## 4. Status Enums And Lifecycle Enums

### AI execution
- `queued`
- `running`
- `completed`
- `failed`
- `partial`
- `requires_review`
- `cancelled`

### Automation execution
- `queued`
- `scheduled`
- `running`
- `completed`
- `failed`
- `partial`
- `cancelled`
- `requires_review`

### Prompt version
- `draft`
- `pending_approval`
- `approved`
- `active`
- `rejected`
- `archived`

### Provider health
- `unknown`
- `healthy`
- `warning`
- `unhealthy`

### Failure item
- `new`
- `triaged`
- `retrying`
- `resolved`
- `moved_to_dead_letter`
- `ignored`

### Approval item
- `pending`
- `approved`
- `rejected`
- `expired`
- `cancelled`

## 5. Suggested Indexes

High-value indexes:
- `(tenant_id, status)` on requests, runs, failures, approvals
- `(source_entity_type, source_entity_id)` on AI requests and automation runs
- `(trigger_event, status, priority_order)` on automation rules
- `(tenant_id, module_scope, use_case_key)` on routing rules and prompt templates
- `(tenant_id, status, scheduled_for)` on scheduled actions and automation runs
- `(tenant_id, status, approver_role)` on approvals
- `(retryable, next_retry_at)` on failures
- unique idempotency indexes on AI requests and automation runs

Operational note:
- execution tables will become append-heavy; optimize for recent-status lookups and source-entity lookup
- consider monthly partitioning later for audit and execution history if volume grows materially

## 6. Soft Delete / Audit Strategy

Soft delete:
- providers
- models
- prompt templates
- automation rules
- connectors

No soft delete:
- execution requests/results
- execution artifacts
- execution reviews
- failures
- dead-letter items
- approvals
- audit logs

Audit rules:
- every toggle, approval, reject, retry, cancel, activation, archive, provider-disable, and settings update writes an audit log
- execution lifecycle transitions are stored on execution rows and optionally mirrored to audit logs for sensitive actions

## 7. Service Layer Boundaries

### `provider_router.py`
- resolve provider/model using tenant settings, routing rules, health, and fallback order

### `prompt_registry_service.py`
- fetch active approved prompt version
- enforce prompt activation rules
- support test runs

### `ai_execution_service.py`
- create request
- validate eligibility
- build execution context
- dispatch Celery task
- persist result/review state

### `automation_rule_service.py`
- resolve matching rules for an event
- evaluate conditions
- create run records
- dispatch actions or approvals

### `approval_service.py`
- create approval queue item
- approve/reject/apply decision
- prevent double-decision

### `failure_service.py`
- classify failure
- schedule retry
- create dead-letter items
- resolve or ignore operator workflows

### `tenant_settings_service.py`
- apply safe defaults
- validate tenant overrides

### `connector_service.py`
- validate connector enablement and fallback behavior

### `audit_service.py`
- write immutable operational audit records

## 8. Celery / Task Execution Structure

Task groups:
- `execute_ai_request`
- `execute_automation_rule`
- `retry_ai_request`
- `retry_automation_run`
- `process_dead_letter_requeue`
- `health_check_provider`
- `scheduled_automation_dispatch`
- `recompute_intelligence_metrics`

Idempotency strategy:
- every execution request/run gets deterministic `idempotency_key` / `dedupe_key`
- consumer checks existing open/completed execution before enqueue
- Celery task re-checks lock before execution

Locking strategy:
- use Redis or DB-backed distributed lock keyed by execution id / dedupe key
- scheduled dispatcher locks per scheduled-action id

Duplicate prevention:
- event consumer derives dedupe key from `(tenant, source_event, source_entity_type, source_entity_id, rule/prompt/use_case, rounded time window if needed)`
- rule-level `duplicate_window_seconds` enforced

## 9. API Contracts

### Overview
`GET /api/v1/intelligence/overview/`
- purpose: operational summary across health, failures, queues, approvals
- actors: platform admin, tenant admin, HR manager, viewer
- response:
  - `provider_health`
  - `queued_ai_count`
  - `queued_automation_count`
  - `failed_count`
  - `pending_approvals`
  - `tenant_enablement`

### Providers / Models
`GET /api/v1/intelligence/providers/`
- purpose: list provider definitions
- actors: platform admin, tenant admin read-only if tenant-scoped

`GET /api/v1/intelligence/models/`
- purpose: list models and capabilities

`PUT /api/v1/intelligence/providers/{id}/`
- actors: platform admin, tenant admin for tenant-owned record
- body:
  - `status`
  - `timeout_seconds`
  - `priority_order`
  - `metadata_json`

`PUT /api/v1/intelligence/models/{id}/`
- body:
  - `status`
  - `cost_class`
  - `quality_tier`
  - `latency_tier`

### Prompts
`GET /api/v1/intelligence/prompts/`
- actors: admin, governance, approved viewers

`POST /api/v1/intelligence/prompts/`
- body:
  - `prompt_key`
  - `prompt_title`
  - `module_scope`
  - `use_case_key`
  - `description`
  - `tenant_override_allowed`

`GET /api/v1/intelligence/prompts/{id}/`
- returns template + versions + scopes

`PUT /api/v1/intelligence/prompts/{id}/`
- update non-terminal prompt metadata

`POST /api/v1/intelligence/prompts/{id}/approve/`
- actors: platform admin or governance-capable approver
- body:
  - `version_id`
  - `comment`
- side effect:
  - marks version approved
  - may activate if requested and valid

`POST /api/v1/intelligence/prompts/{id}/archive/`
- side effect:
  - archives non-active template or version

`POST /api/v1/intelligence/prompts/{id}/test/`
- body:
  - `version_id`
  - `test_input_json`
- response:
  - `test_run_id`
  - `run_status`

### Automations
`GET /api/v1/intelligence/automations/`
- list rules scoped to tenant/platform permission

`POST /api/v1/intelligence/automations/`
- body:
  - `rule_key`
  - `rule_title`
  - `module_scope`
  - `trigger_event`
  - `mode`
  - `conditions`
  - `actions`
  - `scopes`

`GET /api/v1/intelligence/automations/{id}/`
- returns rule + conditions + actions + scopes

`PUT /api/v1/intelligence/automations/{id}/`
- update mutable rule fields

`POST /api/v1/intelligence/automations/{id}/toggle/`
- body:
  - `status` (`active`, `paused`, `inactive`)

`POST /api/v1/intelligence/automations/{id}/simulate/`
- body:
  - `event_payload_json`
- response:
  - evaluated conditions
  - planned actions
  - warnings

`GET /api/v1/intelligence/automations/{id}/runs/`
- execution history for the rule

### Executions
`GET /api/v1/intelligence/executions/ai/`
- filters:
  - `status`
  - `module_scope`
  - `use_case_key`
  - `source_entity_type`
  - `source_entity_id`

`GET /api/v1/intelligence/executions/automation/`
- similar filters

`GET /api/v1/intelligence/executions/{id}/`
- returns unified detail shape with execution-type-specific sections

`POST /api/v1/intelligence/executions/{id}/retry/`
- actors: tenant admin, operations manager, limited recruiter if allowed
- side effect:
  - creates retry attempt or scheduled retry

`POST /api/v1/intelligence/executions/{id}/cancel/`
- allowed only for non-terminal queued/scheduled/running safe states

`POST /api/v1/intelligence/executions/{id}/approve/`
- applies approval-required result or action

`POST /api/v1/intelligence/executions/{id}/reject/`
- rejects approval-required result or action

### Failures / Dead Letter
`GET /api/v1/intelligence/failures/`
- purpose: operator failure list

`GET /api/v1/intelligence/dead-letter/`
- purpose: terminal issues needing requeue or close

`POST /api/v1/intelligence/failures/{id}/retry/`
- side effect: schedules retry if allowed

`POST /api/v1/intelligence/failures/{id}/resolve/`
- body: `resolution_note`

`POST /api/v1/intelligence/dead-letter/{id}/requeue/`
- side effect: creates new execution attempt with link to dead-letter source

### Settings
`GET /api/v1/intelligence/settings/`
- returns tenant settings for current tenant

`PUT /api/v1/intelligence/settings/`
- body:
  - `ai_enabled`
  - `automation_enabled`
  - `default_approval_mode`
  - `allowed_provider_ids_json`
  - `feature_flags_json`
  - `retry_policy_overrides_json`
  - `connector_enablement_json`

### Approvals
`GET /api/v1/intelligence/approvals/`
- list pending and recent approvals

`GET /api/v1/intelligence/approvals/{id}/`
- detail payload

`POST /api/v1/intelligence/approvals/{id}/approve/`
- body: `comment`

`POST /api/v1/intelligence/approvals/{id}/reject/`
- body: `comment`

## 10. Permissions Model

Roles:
- `platform_admin`
- `tenant_admin`
- `hr_manager`
- `recruiter`
- `viewer`
- `candidate`

Permission map:

`view ICC overview`
- platform admin, tenant admin, hr manager, viewer

`manage prompts`
- platform admin, tenant admin where tenant override allowed

`approve prompts`
- platform admin, governance-authorized tenant admin only

`manage providers`
- platform admin only for platform providers
- tenant admin only for tenant-scoped overrides

`manage automation rules`
- platform admin, tenant admin

`toggle automation`
- platform admin, tenant admin

`view executions`
- platform admin, tenant admin, hr manager, recruiter scoped

`retry failed executions`
- platform admin, tenant admin, operations-capable hr manager
- recruiter only if rule/use-case explicitly permits manual rerun

`view failures`
- platform admin, tenant admin, hr manager

`resolve failures`
- platform admin, tenant admin

`view dead letter items`
- platform admin, tenant admin

`approve AI outputs`
- tenant admin, hr manager with approval permission, governance role

`manage tenant intelligence settings`
- tenant admin

`candidate access`
- none by default

## 11. Retry And Failure Logic

Retryable categories:
- provider timeout
- transient network/system exception
- temporary provider unhealthy
- delayed dependency ready soon

Non-retryable by default:
- invalid prompt schema
- invalid response validation failure with deterministic error
- connector disabled
- tenant setting disabled
- permission denied
- approval rejected
- rule misconfiguration

Retry policy:
- exponential backoff
- max retries from routing rule or tenant override or provider default
- after exhaustion:
  - mark execution failed
  - create/update failure item
  - move to dead-letter if appropriate

Manual rerun:
- must create a new execution attempt
- never mutate historical attempt into fresh state

## 12. Approval Workflow Model

Modes:
- `auto_apply`
- `suggestion_only`
- `approval_required`

Approval queue supports:
- AI output approvals
- automation action approvals
- prompt activation approvals
- high-risk rule enablement approvals
- rerun authorization where needed

Flow:
1. originating object marked `requires_approval`
2. approval queue item created
3. approver approves or rejects once
4. if approved, application action executes and `applied_at` recorded
5. if rejected, source object gets final disposition `rejected` or `not_applied`

No double-decision allowed.

## 13. Tenant Scoping Rules

Rules:
- all execution, failure, approval, and settings records must be tenant-scoped except approved platform-global config
- platform-global prompts/providers/models must still be resolved through tenant policy before use
- tenant cannot route to platform-disabled provider
- tenant overrides only allowed where template/rule explicitly permits it
- cross-tenant visibility is never allowed for executions, failures, or approvals

## 14. Validation Rules

Hard validations:
- only approved prompt versions can become active
- only active providers/models can be routed
- automation cannot activate with invalid conditions or actions
- retry cannot occur on terminal cancelled or resolved states
- tenant cannot use provider not in allowed list
- approval item cannot be approved/rejected twice
- structured output must validate before auto-apply
- high-risk rules must use `approval_required`
- `auto_apply` cannot be enabled for banned use cases such as stage movement or rejection automation in phase 1

## 15. Recommended Phased Implementation Order

### Phase 1
- tenant settings
- providers/models/provider configs
- prompt templates and versions
- AI execution requests/results
- automation rules and execution runs
- connectors
- basic overview endpoints

### Phase 2
- failures
- dead-letter
- approvals
- prompt test runs
- model routing rules
- scheduled automation actions

### Phase 3
- simulation mode
- richer tenant overrides
- provider health tasks
- advanced audit dashboards
- analytics/metrics recomputation

## 16. Anti-Patterns To Reject

Reject:
- one giant mixed execution table
- prompts stored only in Python constants
- provider-specific fields leaking into business modules
- missing audit trail for approvals and toggles
- rule execution without idempotency
- infinite retry loops
- tenant setting bypass through service shortcuts
- approval-required actions applied automatically

## 17. Final Recommendation

This backend should be built as a separate platform app with:
- normalized configuration tables
- split AI and automation execution histories
- explicit failure and approval objects
- tenant-aware routing and settings
- event-driven async execution
- strict human override paths

The design is intentionally biased toward:
- auditability
- failure isolation
- replaceable providers
- safe phased rollout
- business-module independence
