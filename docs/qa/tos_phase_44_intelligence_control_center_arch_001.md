# TOS-ICC-ARCH-001

## 1. Module Definition

Preferred product name:
- `Intelligence Control Center`

Locked internal implementation name:
- `orchestration_center`

Reason:
- `ICC` is already used across TOS for `Interview Command Center`
- product naming can stay `Intelligence Control Center`
- code, routes, event namespaces, and backend app labels must avoid collision

Recommended Django app:
- `apps/orchestration_center/`

Recommended UI menu label:
- `Intelligence Control Center`

Recommended route prefix:
- `/intelligence`

Recommended event namespace:
- `intelligence.*`

## 2. Purpose And Boundaries

Purpose:
- provide one control plane for all AI and automation execution across TOS
- isolate failures from business flows
- centralize prompts, provider routing, rules, retries, approvals, logging, toggles, and tenant controls
- expose operational visibility and human override

Hard boundary:
- business modules remain system-of-record for business entities
- Intelligence Control Center owns orchestration only

ICC owns:
- AI execution requests and outputs
- automation rule evaluation and execution
- prompt registry and approval
- provider/model routing
- failure handling and retries
- manual rerun and skip controls
- governance and approvals for sensitive actions
- tenant-level AI/automation settings
- execution monitoring and audit

ICC does not own:
- candidates
- jobs
- applications
- interviews
- offers
- business-stage truth

## 3. Architecture Overview

Control pattern:
- `Manual Core Flow -> Event Emission -> ICC Orchestration -> Optional AI/Automation Execution -> Safe Fallback -> Audit`

Runtime model:
- business modules persist valid manual action first
- business module emits domain event
- ICC connector consumes event
- ICC decides whether AI assist, automation, approval, or no-op applies
- ICC executes async by default
- ICC writes execution records and outputs
- business module may consume suggestion/result later, but never depends on it for core continuity

Core architecture layers:
- Connector Layer
- Event Intake Layer
- Orchestration Layer
- AI Execution Layer
- Automation Engine
- Prompt Registry
- Provider Routing Layer
- Governance Layer
- Monitoring and Operations Layer
- Fallback and Manual Override Layer
- Audit Layer

Consistency rules:
- strict consistency for business writes stays inside source business module
- eventual consistency is acceptable for AI suggestions, automations, dashboards, and analytics
- ICC must never be the only write path for user-critical business progression

## 4. Ownership Split: ICC vs Business Modules

Jobs:
- Jobs owns create/edit/publish and status truth
- ICC owns JD enhancement, matching trigger orchestration, reminders, escalation workflows

Candidates:
- Candidate module owns profile, passport, state, and source truth
- ICC owns resume parsing execution, profile enrichment suggestions, matching requests

Pipeline:
- Pipeline owns application progression and manual stage moves
- ICC owns ranking suggestions, reminder automations, SLA escalations, delayed follow-up actions

Interviews:
- Interview module owns schedule/completion/feedback truth
- ICC owns transcript summarization, interview intelligence, reminder automations, no-feedback escalations

Communication:
- Communication module owns sent-message records, templates, and manual send
- ICC owns draft generation, follow-up sequences, trigger-based communication orchestration

Offers:
- Offer/HDC modules own approvals, compensation, release, acceptance, joining truth
- ICC owns drafting assistance, reminder automation, risk alerts, operational escalations

## 5. Failure Isolation Strategy

Locked principle:
- no user-critical flow fails because AI or automation failed

Failure handling rules:
- persist business action first if valid
- never block manual action on provider availability
- mark orchestration execution as failed independently
- show non-blocking warning only where needed
- create retryable failure record
- route to dead-letter if retries exhausted
- preserve manual continue path

Examples:
- resume parser failure cannot block candidate creation
- candidate ranking failure cannot block recruiter shortlist
- interview summary failure cannot block interview completion
- automation queue failure cannot block stage movement
- communication drafting failure cannot block manual email send

Required user experience:
- warning, not blocker, for assistive failures
- explicit `Run again`, `Skip`, `Continue manually`, or `Approve manually` actions

## 6. Event Integration Map

`candidate.created`
- listener: `CandidateCreatedListener`
- trigger: AI resume/profile enrichment, optional automation
- execution: async
- failure: candidate remains created, enrichment marked failed
- user sees: optional enrichment warning
- audit: request, provider, prompt version, failure reason

`candidate.updated`
- listener: `CandidateUpdatedListener`
- trigger: re-enrichment, re-match scoring
- execution: async
- failure: update persists, AI request fails independently

`application.submitted`
- listener: `ApplicationSubmittedListener`
- trigger: ranking, recruiter notification, SLA timer automation
- execution: async
- failure: application remains submitted

`application.stage_changed`
- listener: `ApplicationStageChangedListener`
- trigger: reminders, communication sequences, candidate ranking refresh, downstream interview trigger suggestions
- execution: async
- failure: stage move remains valid

`application.shortlisted`
- listener: `ApplicationShortlistedListener`
- trigger: interview setup automation, draft communication
- execution: async

`interview.scheduled`
- listener: `InterviewScheduledListener`
- trigger: reminders, prep material sequences, AI prep suggestions
- execution: async

`interview.completed`
- listener: `InterviewCompletedListener`
- trigger: summarization, transcript analysis, follow-up reminders for missing feedback
- execution: async
- failure: interview stays completed

`interview.feedback_submitted`
- listener: `InterviewFeedbackSubmittedListener`
- trigger: score synthesis, summary assist, decision support signals
- execution: async

`job.created`
- listener: `JobCreatedListener`
- trigger: JD enhancement suggestion, approval reminder automation
- execution: async

`job.approved`
- listener: `JobApprovedListener`
- trigger: publish reminder, sourcing automation, matching refresh
- execution: async

`job.published`
- listener: `JobPublishedListener`
- trigger: candidate matching, notification sequences, agency distribution reminders
- execution: async

`agency.candidate_submitted`
- listener: `AgencyCandidateSubmittedListener`
- trigger: intake automation, ranking assist, notification orchestration
- execution: async

`deadline.overdue`
- listener: `DeadlineOverdueListener`
- trigger: escalation automation
- execution: async

`passport.updated`
- listener: `PassportUpdatedListener`
- trigger: re-parse or data-quality automation
- execution: async

`message.sent`
- listener: `MessageSentListener`
- trigger: follow-up timers, sequence advancement
- execution: async

## 7. Backend Module Structure

Recommended structure:

```text
apps/orchestration_center/
  models.py
  admin.py
  api/
    serializers.py
    views.py
    urls.py
  services/
    ai_execution_service.py
    automation_execution_service.py
    rule_engine_service.py
    provider_router.py
    prompt_registry_service.py
    fallback_service.py
    approval_service.py
    audit_service.py
    connector_service.py
  consumers/
    event_consumers.py
  tasks/
    ai_tasks.py
    automation_tasks.py
    retry_tasks.py
    health_tasks.py
  selectors/
    overview_selectors.py
    execution_selectors.py
    governance_selectors.py
  policies/
    ai_policies.py
    automation_policies.py
    approval_policies.py
  constants/
    statuses.py
    actions.py
    providers.py
  signals/
    execution_signals.py
```

Primary services:
- `AIExecutionService`: request creation, provider routing, output validation, output persistence
- `AutomationExecutionService`: rule dispatch, action scheduling, execution records
- `RuleEngineService`: condition evaluation and deduplication
- `ProviderRouter`: provider/model selection, timeout, fallback routing
- `PromptRegistryService`: prompt resolution, versioning, approval enforcement
- `FallbackService`: skip/manual/retry/dead-letter behaviors
- `ApprovalService`: suggestion-only, approval-required, auto-execute policy handling
- `AuditService`: immutable operational audit records

Worker pattern:
- sync only for low-risk validation or request registration
- async for provider calls, delayed automation, retries, health checks, recurring scans

## 8. Database Design Proposal

### `ai_providers`
- `id`
- `tenant_id` nullable for platform-level default
- `provider_key`
- `provider_name`
- `provider_type`
- `status` (`active`, `inactive`, `degraded`, `disabled`)
- `base_url`
- `credential_ref`
- `timeout_seconds`
- `max_retries`
- `priority_order`
- `supports_structured_output`
- `is_fallback_enabled`
- audit fields

Indexes:
- `(tenant_id, provider_key)`
- `(status, priority_order)`

### `ai_models`
- `id`
- `provider_id`
- `tenant_id` nullable
- `model_key`
- `model_name`
- `capability_type`
- `status`
- `cost_class`
- `max_tokens`
- `supports_json_mode`
- `supports_tools`
- `latency_tier`
- audit fields

Indexes:
- `(provider_id, status)`
- `(tenant_id, capability_type, status)`

### `prompt_templates`
- `id`
- `tenant_id` nullable
- `module_scope`
- `use_case_key`
- `name`
- `status` (`draft`, `approved`, `active`, `archived`)
- `owner_role`
- `approval_required`
- `fallback_template_id` nullable
- audit fields

Indexes:
- `(tenant_id, module_scope, use_case_key)`
- `(status, module_scope)`

### `prompt_versions`
- `id`
- `prompt_template_id`
- `version_number`
- `system_prompt`
- `user_prompt_template`
- `output_schema`
- `validation_rules`
- `status`
- `approved_by`
- `approved_at`
- `rollback_of_version_id` nullable
- audit fields

Indexes:
- `(prompt_template_id, version_number desc)`
- `(status, approved_at)`

### `automation_rules`
- `id`
- `tenant_id` nullable
- `module_scope`
- `rule_key`
- `name`
- `trigger_event`
- `mode` (`suggestion_only`, `auto_execute`, `approval_required`)
- `status` (`active`, `paused`, `draft`, `archived`)
- `priority`
- `is_builtin`
- `schedule_type` (`event`, `delayed`, `recurring`)
- `approval_policy_key` nullable
- audit fields

Indexes:
- `(tenant_id, module_scope, status)`
- `(trigger_event, status, priority)`

### `automation_rule_conditions`
- `id`
- `rule_id`
- `field_path`
- `operator`
- `expected_value_json`
- `condition_group`
- `sequence_order`

Indexes:
- `(rule_id, sequence_order)`

### `automation_rule_actions`
- `id`
- `rule_id`
- `action_type`
- `action_config_json`
- `requires_approval`
- `delay_seconds`
- `sequence_order`

Indexes:
- `(rule_id, sequence_order)`

### `automation_executions`
- `id`
- `tenant_id`
- `rule_id`
- `event_name`
- `source_module`
- `source_entity_type`
- `source_entity_id`
- `status` (`queued`, `running`, `completed`, `failed`, `partial`, `cancelled`, `requires_review`)
- `dedupe_key`
- `scheduled_for`
- `started_at`
- `completed_at`
- `retry_count`
- `last_error_code`
- `last_error_message`
- `result_summary_json`
- audit fields

Indexes:
- `(tenant_id, status, scheduled_for)`
- `(event_name, status)`
- `(source_entity_type, source_entity_id)`
- unique `(dedupe_key)` where not null

### `ai_executions`
- `id`
- `tenant_id`
- `module_scope`
- `use_case_key`
- `source_entity_type`
- `source_entity_id`
- `prompt_version_id`
- `provider_id`
- `model_id`
- `status`
- `mode` (`suggestion_only`, `auto_apply`, `approval_required`)
- `confidence_score`
- `cost_estimate`
- `request_payload_ref`
- `response_payload_ref`
- `validated_output_json`
- `requires_review`
- `review_status`
- `started_at`
- `completed_at`
- `retry_count`
- `last_error_code`
- `last_error_message`
- audit fields

Indexes:
- `(tenant_id, module_scope, status)`
- `(source_entity_type, source_entity_id)`
- `(prompt_version_id, created_at desc)`
- `(review_status, status)`

### `execution_failures`
- `id`
- `tenant_id`
- `execution_type` (`ai`, `automation`)
- `execution_id`
- `failure_stage`
- `error_code`
- `error_message`
- `retry_eligible`
- `retry_after`
- `resolved_status`
- `resolved_by`
- audit fields

Indexes:
- `(tenant_id, execution_type, resolved_status)`
- `(retry_eligible, retry_after)`

### `dead_letter_items`
- `id`
- `tenant_id`
- `execution_type`
- `execution_id`
- `reason_code`
- `payload_ref`
- `status` (`open`, `retried`, `dismissed`, `resolved`)
- `resolved_by`
- `resolved_at`
- audit fields

Indexes:
- `(tenant_id, status)`

### `module_connectors`
- `id`
- `tenant_id` nullable
- `module_name`
- `connector_key`
- `status`
- `supported_events_json`
- `supported_ai_hooks_json`
- `supported_automation_triggers_json`
- `fallback_contract_json`
- audit fields

Indexes:
- `(module_name, status)`

### `tenant_intelligence_settings`
- `id`
- `tenant_id`
- `ai_enabled`
- `automation_enabled`
- `suggestion_only_default`
- `provider_policy_json`
- `restricted_actions_json`
- `allowed_modules_json`
- `notification_preferences_json`
- audit fields

Indexes:
- unique `(tenant_id)`

### `approval_queue_items`
- `id`
- `tenant_id`
- `approval_type`
- `execution_type`
- `execution_id`
- `source_module`
- `source_entity_type`
- `source_entity_id`
- `status` (`pending`, `approved`, `rejected`, `expired`, `cancelled`)
- `assigned_role`
- `assigned_user_id` nullable
- `decision_reason`
- `decided_at`
- audit fields

Indexes:
- `(tenant_id, status, assigned_role)`
- `(execution_type, execution_id)`

### `execution_audit_logs`
- `id`
- `tenant_id`
- `execution_type`
- `execution_id`
- `event_type`
- `actor_type`
- `actor_id`
- `before_state_json`
- `after_state_json`
- `metadata_json`
- `created_at`

Indexes:
- `(tenant_id, execution_type, execution_id, created_at)`

Soft delete:
- use soft delete for templates, rules, connectors, and settings history
- do not soft delete execution records or audit logs

## 9. API Contract Proposal

### Overview
- `GET /api/v1/intelligence/overview/`
  - tenant admin, system admin, governance viewer

### Automations
- `GET /api/v1/intelligence/automations/`
- `POST /api/v1/intelligence/automations/`
- `PUT /api/v1/intelligence/automations/{id}/`
- `POST /api/v1/intelligence/automations/{id}/toggle/`
- `POST /api/v1/intelligence/automations/{id}/run-test/`
- `GET /api/v1/intelligence/automations/{id}/executions/`

Permissions:
- recruiter: view only within tenant where allowed
- tenant admin: full tenant control
- system admin: platform control
- governance reviewer: view plus approval actions where policy-bound

### AI Actions
- `GET /api/v1/intelligence/ai-actions/`
- `POST /api/v1/intelligence/ai-actions/{use_case}/run/`
- `POST /api/v1/intelligence/ai-actions/{execution_id}/approve/`
- `POST /api/v1/intelligence/ai-actions/{execution_id}/reject/`
- `POST /api/v1/intelligence/ai-actions/{execution_id}/retry/`

### Prompts
- `GET /api/v1/intelligence/prompts/`
- `POST /api/v1/intelligence/prompts/`
- `PUT /api/v1/intelligence/prompts/{id}/`
- `GET /api/v1/intelligence/prompts/{id}/versions/`
- `POST /api/v1/intelligence/prompts/{id}/approve/`
- `POST /api/v1/intelligence/prompts/{id}/archive/`
- `POST /api/v1/intelligence/prompts/{id}/test/`

Permissions:
- prompt edit: system admin or designated tenant AI admin
- prompt approve: governance-approved admin role only

### Providers And Models
- `GET /api/v1/intelligence/providers/`
- `PUT /api/v1/intelligence/providers/{id}/`
- `GET /api/v1/intelligence/models/`
- `PUT /api/v1/intelligence/models/{id}/`
- `POST /api/v1/intelligence/providers/{id}/disable/`

Permissions:
- system admin only for platform providers
- tenant admin for tenant-scoped overrides

### Executions And Failures
- `GET /api/v1/intelligence/executions/`
- `GET /api/v1/intelligence/executions/{id}/`
- `POST /api/v1/intelligence/executions/{id}/retry/`
- `POST /api/v1/intelligence/executions/{id}/cancel/`
- `GET /api/v1/intelligence/failures/`
- `GET /api/v1/intelligence/dead-letter/`
- `POST /api/v1/intelligence/dead-letter/{id}/requeue/`

### Governance
- `GET /api/v1/intelligence/approvals/`
- `POST /api/v1/intelligence/approvals/{id}/approve/`
- `POST /api/v1/intelligence/approvals/{id}/reject/`
- `GET /api/v1/intelligence/settings/`
- `PUT /api/v1/intelligence/settings/`

Visibility rules:
- recruiters can see only operationally relevant executions for their tenant/module scopes
- tenant admins can see tenant-level ICC
- governance reviewers can see approval-required and restricted actions
- system admins can see platform-wide providers, health, global prompt registry

## 10. UI/Menu/Screen Map

Main menu:
- `Intelligence Control Center`

Screens:

### Overview
- AI health summary
- automation health summary
- failed execution cards
- queue depth
- tenant enablement state
- provider health

### Automations
- rules table
- enabled/paused states
- next run and last run
- test mode
- detail drawer with conditions/actions

### AI Actions
- use case list
- execution history
- confidence and review flags
- manual rerun
- approve/reject actions

### Prompt Studio
- prompt list
- version diff view
- status tabs
- test console
- output comparison

### Models & Providers
- providers grid
- health and timeout config
- model routing rules
- fallback chain detail

### Queue & Failures
- queued, failed, dead-letter tabs
- stuck execution detection
- retry and requeue controls

### Governance & Approvals
- pending approvals
- restricted actions
- tenant overrides
- high-risk AI uses

### Settings
- feature toggles
- connector status
- notification preferences
- tenant AI/automation defaults

UI pattern:
- list/detail split
- summary cards
- execution badges
- dense operational tables
- non-technical wording at top layer, technical detail in drawers/panels

## 11. Permissions And Governance Model

Roles:
- `system_admin`
- `tenant_admin`
- `governance_reviewer`
- `operations_manager`
- `recruiter`
- `viewer`

Key controls:
- only system admin can disable platform providers
- only tenant admin can enable or disable tenant AI features
- prompt approval requires governance-capable role
- approval-required AI outputs cannot auto-apply without approval record
- restricted automation policies can be enabled only by tenant admin or system admin
- recruiters can trigger allowed manual reruns, but cannot change routing or approval policy

Execution modes:
- `suggestion_only`
- `auto_execute`
- `approval_required`

Phase 1 rules:
- stage movement: never AI-only
- rejection automation: approval-required
- ranking: suggestion-only
- interview summary: auto-execute allowed
- reminder automations: auto-execute allowed

## 12. Execution Lifecycle Definitions

AI execution lifecycle:
- `queued`
- `running`
- `completed`
- `failed`
- `partial`
- `requires_review`
- `cancelled`

Automation execution lifecycle:
- `queued`
- `scheduled`
- `running`
- `completed`
- `failed`
- `partial`
- `cancelled`
- `requires_review`

Retry rules:
- retry only idempotent or deduplicated actions
- exponential backoff for provider/network failures
- no blind retry for validation failures or approval rejections
- dead-letter after retry exhaustion

Validation steps for AI:
- prompt version resolve
- context build
- provider route
- response schema validation
- confidence capture
- review policy evaluation
- output persistence

## 13. Phase-Wise Implementation Order

### Phase 1
- app skeleton
- execution models
- provider/model registry
- prompt registry
- execution logging
- tenant settings
- overview APIs

### Phase 2
- event consumers for jobs, candidates, pipeline, interviews, communication
- AI request lifecycle
- automation rule engine for built-in rules
- retry and dead-letter pipeline

### Phase 3
- UI overview, automations, failures, executions
- governance approvals
- prompt studio basic versioning and testing

### Phase 4
- provider fallback chains
- module connectors
- tenant overrides
- manual rerun and skip UX

### Phase 5
- advanced prompt experimentation
- approval analytics
- custom tenant rules
- richer monitoring and health

## 14. Risks / Anti-Patterns To Avoid

Reject explicitly:
- embedding AI logic separately inside each module
- making business modules depend on ICC for mandatory progression
- prompts hardcoded in frontend or business services
- automations without audit trail
- AI outputs applied without validation
- failures without retry, logging, or dead-lettering
- stage movement controlled only by AI
- approval bypass for sensitive actions
- provider-specific lock-in inside business services

Additional risks:
- naming collision with Interview Command Center if internal key is also `icc`
- over-centralization that turns ICC into a hidden business logic owner
- sync AI calls inside request/response flows
- weak deduplication causing repeated automations
- poor tenant scoping in logs or prompt selection

## 15. Final Recommendation On Naming And Rollout Strategy

Naming:
- product/UI label: `Intelligence Control Center`
- internal app label: `orchestration_center`
- operational shorthand in code/docs: `intel-control`

Rollout strategy:
- launch as platform infrastructure, not as mandatory dependency
- start with suggestion-only and operational automations
- keep sensitive actions in approval-required mode
- integrate module by module through explicit connectors and event contracts
- measure failures, retry behavior, and manual override usage before expanding automation scope

Final recommendation:
- make this the single control plane for all AI and automation
- keep it optional from the business-flow perspective
- keep business modules authoritative
- keep every execution auditable, tenant-scoped, retryable, and human-overridable
