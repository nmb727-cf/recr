# Phase 15: AI Builder Flow Generation Engine

Prompt ID: `ICC-AI-BUILDER-FLOW-GENERATION-15`  
Phase: `Interview Command Center / AI Builder / Phase 15`  
Module: `AI Builder Flow Generation Engine`

## Scope

Tenant-scoped structured flow generation engine for creating reusable interview flow artifacts for:

- interview round sequences
- multi-step hiring flows
- composite interview journeys
- async + live mixed journeys
- engine-to-engine transitions
- score / threshold based progression logic
- manual review gates
- branch-ready flow structures
- rejection / retry / hold paths
- recruiter-friendly flow variants

Candidate has no access. Output is always structured flow objects, never narrative-only sequencing.

## 1. System Architecture

- Shared engine: `AIFlowGenerationEngine`
- Core components:
  - Flow generation engine
  - Context-to-flow transformer
  - Step sequencing resolver
  - Execution engine selection layer
  - Transition rule generator
  - Review gate generator
  - Branch / exception path generator
  - Flow variant generator
  - Refinement / regeneration layer
  - Validation / compatibility layer
  - Review / approval handoff layer
  - Version / snapshot engine
  - Explainability / audit layer
  - Composite flow mapping layer

Architecture layers:

- context intake layer
- intent resolution layer
- flow schema layer
- step assembly layer
- transition logic layer
- variant layer
- validation layer
- review layer
- publish layer
- audit layer

Pipeline:

1. Consume structured builder context from AI Builder Foundation or Wizard.
2. Resolve target flow type and target use case.
3. Select common flow schema plus target branching mode.
4. Generate structured draft flow artifact.
5. Bind or suggest templates, scorecards, engines, transitions, and gates.
6. Optionally generate flow variants.
7. Validate sequencing, mappings, thresholds, branch logic, and policy.
8. Hand off for review, approval, and publish.
9. Publish versioned flow to Flow Engine / Interview Registry.

Generation rules:

- Draft-first only
- Supports:
  - linear flows
  - gated flows
  - branched flows
- Supports reusable flow family / variant model
- Existing flows can be used as seed context for refinement and adaptation
- Tenant defaults and standards shape step order, gate strictness, and engine recommendations

Mapping behavior:

- Generated flows map to:
  - execution engines at step level
  - templates at step level
  - scorecards at step level
  - composite flow engine at orchestration level
- Composite flow engine consumes published flow definition, not draft state

## 2. Database Design

Primary entities:

- `ai_flow_generation_session`
- `ai_flow_generation_run`
- `ai_flow_artifact_draft`
- `ai_flow_step_record`
- `ai_flow_transition_record`
- `ai_flow_branch_record`
- `ai_flow_engine_mapping`
- `ai_flow_template_binding`
- `ai_flow_scorecard_binding`
- `ai_flow_variant_record`
- `ai_flow_validation_log`
- `ai_flow_refinement_record`
- `ai_flow_review_record`
- `ai_flow_publish_record`
- `ai_flow_version_snapshot`
- `ai_flow_explainability_record`
- `ai_flow_audit_log`

Key fields:

- `tenant_id`
- `builder_project_id`
- `builder_session_id`
- `flow_type`
- `target_use_case`
- `role_family`
- `job_function`
- `seniority_level`
- `status`
- `input_context_payload`
- `generated_flow_payload`
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
- `branching_mode`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

Entity purposes:

- `ai_flow_generation_session`: root flow generation session
- `ai_flow_generation_run`: each generation/regeneration run
- `ai_flow_artifact_draft`: structured flow draft payload
- `ai_flow_step_record`: generated step definitions
- `ai_flow_transition_record`: step-to-step transition definitions
- `ai_flow_branch_record`: conditional branch definitions and terminal paths
- `ai_flow_engine_mapping`: execution engine bindings
- `ai_flow_template_binding`: template bindings for steps
- `ai_flow_scorecard_binding`: scorecard bindings for steps
- `ai_flow_variant_record`: variant family records
- `ai_flow_validation_log`: validation outcomes
- `ai_flow_refinement_record`: manual edits and partial regenerations
- `ai_flow_review_record`: review and approval workflow
- `ai_flow_publish_record`: publish action records
- `ai_flow_version_snapshot`: immutable version snapshots
- `ai_flow_explainability_record`: rationale and confidence artifacts
- `ai_flow_audit_log`: end-to-end audit trail

## 3. API Structure

**Generation APIs**

- Create flow generation session
- Attach builder context
- Generate flow draft
- Generate multiple flow variants
- Regenerate selected step or transition
- Refine flow draft
- Clone flow into new draft
- Adapt existing flow for new role / level / hiring intent
- Fetch generated flow
- Fetch flow variants
- Compare variants
- Fetch explainability summary

**Validation APIs**

- Validate generated flow
- Validate execution engine compatibility
- Validate template bindings
- Validate scorecard bindings
- Validate transition / threshold logic
- Validate composite flow compatibility
- Fetch validation issues
- Mark validation resolved

**Review / publish APIs**

- Submit flow for review
- Assign reviewer
- Add review comments
- Request revision
- Approve flow draft
- Reject flow draft
- Publish flow
- Rollback flow version
- Deactivate flow if needed
- Fetch flow history

**Mapping APIs**

- Map flow to composite flow engine
- Map step to execution engine
- Bind template to step
- Bind scorecard to step
- Fetch mapping status

Rules:

- Draft and published behavior remain separate.
- Publish requires validation success and required approvals.
- Stale drafts cannot publish without refresh or revalidation.
- Branching and binding changes create new draft lineage, not silent live mutation.

## 4. UI Architecture

UI includes:

- Flow generation launch screen
- Context summary panel
- Generated flow preview shell
- Step-by-step flow editor
- Transition / gate editor
- Variant comparison view
- Explainability side panel
- Validation issue panel
- Engine mapping panel
- Template / scorecard binding panel
- Review comments drawer
- Version history view
- Publish confirmation flow

Key modes:

1. Generate New Flow
2. Refine Existing Flow
3. Create Flow Variant
4. Compare Alternatives
5. Validate and Publish

UI rules:

- enterprise layout
- structured editable artifact view
- AI suggestion clearly marked
- strong separation of draft vs live flow
- validation visible before publish
- no black-box activation

## 5. Execution Flow

1. User provides builder context or opens wizard result.
2. Flow Generation Engine receives structured context.
3. Engine resolves target flow schema and branching mode.
4. AI generates structured draft flow.
5. Variants are generated if requested.
6. User previews and refines flow.
7. Validation runs.
8. Review and approval happen if required.
9. Flow publishes.
10. Published flow becomes available in Flow Engine / Interview Registry.
11. Composite Flow Engine and execution engines consume published flow.
12. Version history and audit remain preserved.

Supported flows:

- first-time generation flow
- refine existing flow flow
- generate variant flow
- reject / revise flow
- publish flow
- rollback flow
- invalid engine / binding mapping flow

## 6. Edge Cases

- AI output chooses incompatible step order
- AI assigns wrong execution engine type
- Missing template or scorecard bindings
- Variant generation produces inconsistent transitions
- Existing flow under review gets edited again
- Publish attempted on stale draft
- Tenant standards conflict with generated draft
- Branch logic invalid for target use case
- User regenerates one section causing version conflict
- Rollback requested for flow already in active use
- Generic flow output for niche hiring case
- Reviewer approves older draft instead of latest

Handling rules:

- Invalid step order or engine mapping blocks publish.
- Missing bindings block composite compatibility validation.
- Active-use rollback creates controlled fallback version behavior, not destructive mutation.
- Low-quality or generic flow outputs are warned or blocked based on tenant quality thresholds.

## 7. Enterprise Features

- Draft-first structured flow generation
- Linear, gated, and branched flow support
- Template and scorecard binding-aware generation
- Composite flow compatibility by design
- Tenant standards/defaults injection
- Role / level / intent-specific variants
- Partial step/transition regeneration
- Validation for sequencing, gating, thresholds, and branching
- Explainability and rationale capture
- Controlled publish and rollback
- Full versioning and auditability
- Reusable architecture for future advanced flow intelligence

## 8. Integration Mapping

- `AI Builder Foundation`
- `AI Builder Wizard`
- `Template Generation Engine`
- `Interview Registry`
- `Template Engine`
- `Flow Engine`
- `Scorecard Engine`
- `Question Engine`
- `All Execution Engines`
- `Composite Flow Engine`
- `Analytics Engine`
- `Automation Engine`
- `Audit / Governance Layer`

