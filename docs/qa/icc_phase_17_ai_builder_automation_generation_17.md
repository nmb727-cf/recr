# Phase 17: AI Builder Automation Generation Engine

Prompt ID: `ICC-AI-BUILDER-AUTOMATION-GENERATION-17`  
Phase: `Interview Command Center / AI Builder / Phase 17`  
Module: `AI Builder Automation Generation Engine`

## Scope

Tenant-scoped structured automation generation engine for creating reusable automation artifacts for:

- interview scheduling automation
- reminder automation
- escalation automation
- no-show handling automation
- feedback pending automation
- timeout / expiry automation
- reviewer assignment automation
- score / threshold based automation
- candidate communication automation
- status transition automation
- composite flow progression automation
- exception handling automation

Candidate has no access. Output is always structured automation objects, never free-text-only rule suggestions.

## 1. System Architecture

- Shared engine: `AIAutomationGenerationEngine`
- Core components:
  - Automation generation engine
  - Context-to-automation transformer
  - Trigger generator
  - Condition logic generator
  - Action generator
  - Sequence / dependency engine
  - SLA / timing rule generator
  - Variant generator
  - Refinement layer
  - Validation layer
  - Review / approval layer
  - Version / snapshot engine
  - Explainability layer
  - Mapping layer

Architecture layers:

- context layer
- trigger layer
- condition layer
- action layer
- timing layer
- variant layer
- validation layer
- review layer
- publish layer
- audit layer

Pipeline:

1. Consume structured builder context from AI Builder Foundation or Wizard.
2. Resolve automation type and target scope.
3. Generate trigger set, condition logic, actions, timing rules, and escalation paths.
4. Build structured automation draft with event-driven mappings.
5. Optionally generate automation variants.
6. Validate triggers, actions, timing, conflicts, loops, and tenant policy.
7. Hand off for review, approval, and publish.
8. Publish versioned automation to Automation Layer and Interview Command Center consumers.

Execution safety model:

- Draft-first only
- No automation is auto-activated directly from generation output
- Human review is required before activation where policy requires
- Safety validation blocks recursive, conflicting, noisy, or unsupported automation
- Published automation maps to event-driven runtime only after validation and approval

Compatibility model:

- Supports event-driven architecture
- Supports reusable automation templates and scoped variants
- Integrates with Flow Engine, Execution Engines, Notification Engine, Communication Engine, and Composite Flow Engine
- Existing automation can be used as seed context for refinement and adaptation

## 2. Database Design

Primary entities:

- `ai_automation_generation_session`
- `ai_automation_generation_run`
- `ai_automation_artifact_draft`
- `ai_automation_trigger_record`
- `ai_automation_condition_record`
- `ai_automation_action_record`
- `ai_automation_timing_record`
- `ai_automation_variant_record`
- `ai_automation_validation_log`
- `ai_automation_review_record`
- `ai_automation_publish_record`
- `ai_automation_version_snapshot`
- `ai_automation_explainability_record`
- `ai_automation_audit_log`

Key fields:

- `tenant_id`
- `builder_project_id`
- `builder_session_id`
- `automation_type`
- `target_scope`
- `status`
- `input_context_payload`
- `generated_automation_payload`
- `schema_version`
- `model_used`
- `generation_status`
- `validation_status`
- `review_status`
- `approval_status`
- `publish_status`
- `draft_version`
- `published_version`
- `variant_group_id`
- `mapping_status`
- `safety_status`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

Entity purposes:

- `ai_automation_generation_session`: root generation session
- `ai_automation_generation_run`: each generation/regeneration run
- `ai_automation_artifact_draft`: structured automation draft payload
- `ai_automation_trigger_record`: event trigger definitions
- `ai_automation_condition_record`: condition and gating logic
- `ai_automation_action_record`: actions and destinations
- `ai_automation_timing_record`: SLA, delay, timeout, retry, escalation timing data
- `ai_automation_variant_record`: automation family variants and overrides
- `ai_automation_validation_log`: validation and safety results
- `ai_automation_review_record`: review and approval workflow
- `ai_automation_publish_record`: publish action records
- `ai_automation_version_snapshot`: immutable version snapshots
- `ai_automation_explainability_record`: rationale and confidence summaries
- `ai_automation_audit_log`: full audit trail

## 3. API Structure

**Generation APIs**

- Create automation generation session
- Attach builder context
- Generate automation draft
- Generate multiple automation variants
- Regenerate selected trigger / condition / action / timing block
- Refine automation draft
- Clone automation into new draft
- Adapt existing automation for new scope
- Fetch generated automation
- Fetch automation variants
- Compare variants
- Fetch explainability summary

**Validation APIs**

- Validate generated automation
- Validate trigger compatibility
- Validate condition logic
- Validate action compatibility
- Validate event mapping
- Validate timing / SLA rules
- Validate execution safety
- Fetch validation issues
- Mark validation resolved

**Review / publish APIs**

- Submit automation for review
- Assign reviewer
- Add review comments
- Request revision
- Approve automation draft
- Reject automation draft
- Publish automation
- Rollback automation version
- Deactivate automation if needed
- Fetch automation history

**Mapping APIs**

- Map automation to interview flow
- Map automation to execution engines
- Map automation to communication triggers
- Map automation to composite flow progression
- Fetch mapping status

Rules:

- Draft and published behavior remain separate.
- Publish requires validation success, safety approval, and required human approval.
- Regenerating one trigger or action block creates new draft lineage.
- Older drafts cannot be approved over newer unresolved drafts without explicit override.

## 4. UI Architecture

UI includes:

- Automation generation launch screen
- Context summary panel
- Generated automation preview shell
- Trigger / condition / action editor
- Timing / SLA editor
- Variant comparison view
- Explainability side panel
- Validation issue panel
- Event mapping panel
- Review comments drawer
- Version history view
- Publish confirmation flow

Key modes:

1. Generate New Automation
2. Refine Existing Automation
3. Create Automation Variant
4. Compare Alternatives
5. Validate and Publish

UI rules:

- enterprise layout
- structured editable artifact view
- AI suggestions clearly marked
- strong separation of draft vs live automation
- validation visible before publish
- no black-box activation

## 5. Execution Flow

1. User provides builder context or opens wizard result.
2. Automation Generation Engine receives structured context.
3. Engine resolves target automation schema.
4. AI generates structured draft automation.
5. Variants are generated if requested.
6. User previews and refines automation.
7. Validation runs.
8. Review and approval happen if required.
9. Automation publishes.
10. Published automation becomes available in Automation Layer and Interview Command Center.
11. Flow Engine, Execution Engines, Notifications, and Communication consumers can use it.
12. Version history and audit remain preserved.

Supported flows:

- first-time generation flow
- refine existing automation flow
- generate variant flow
- reject / revise flow
- publish flow
- rollback flow
- invalid trigger / action mapping flow

## 6. Edge Cases

- AI generates conflicting triggers
- AI creates recursive / looping automation
- Invalid timing chain
- Missing event source
- Action not supported by mapped engine
- Duplicate automation already active
- Existing automation under review gets edited again
- Publish attempted on stale draft
- Tenant standards conflict with generated draft
- User regenerates one section causing version conflict
- Rollback requested for automation already actively firing
- Reviewer approves older draft instead of latest

Handling rules:

- Recursive or looping automation is blocked by safety validation.
- Unsupported actions or missing event sources block publish.
- Duplicate active automation raises conflict warning or hard-stop based on tenant policy.
- Active-use rollback creates controlled deactivation/fallback path rather than destructive replacement.

## 7. Enterprise Features

- Draft-first structured automation generation
- Event-driven trigger, condition, action, and timing generation
- SLA and escalation-aware rule design
- Strict safety validation for loops, conflicts, and noisy automations
- Tenant policy and standards injection
- Variant generation by strictness, speed, scope, and operating model
- Partial regeneration of trigger, condition, action, or timing blocks
- Explainability and rationale capture
- Controlled publish and rollback
- Full versioning and auditability
- Reusable architecture for future advanced automation intelligence

## 8. Integration Mapping

- `AI Builder Foundation`
- `AI Builder Wizard`
- `Template Generation Engine`
- `Flow Generation Engine`
- `Scorecard Generation Engine`
- `Interview Registry`
- `Flow Engine`
- `All Execution Engines`
- `Composite Flow Engine`
- `Notification Engine`
- `Communication Engine`
- `Analytics Engine`
- `Automation Engine`
- `Audit / Governance Layer`

