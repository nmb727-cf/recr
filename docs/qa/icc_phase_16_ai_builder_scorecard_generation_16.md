# Phase 16: AI Builder Scorecard Generation Engine

Prompt ID: `ICC-AI-BUILDER-SCORECARD-GENERATION-16`  
Phase: `Interview Command Center / AI Builder / Phase 16`  
Module: `AI Builder Scorecard Generation Engine`

## Scope

Tenant-scoped structured scorecard generation engine for creating reusable evaluation artifacts for:

- competency-based scorecards
- skill-based scorecards
- behavioral scorecards
- leadership scorecards
- technical evaluation scorecards
- multi-round scorecard frameworks
- weighted scoring systems
- pass / fail threshold models
- interviewer guidance notes
- scoring rubric templates

Candidate has no access. Output is always structured scorecard objects.

## 1. System Architecture

- Shared engine: `AIScorecardGenerationEngine`
- Core components:
  - Scorecard generation engine
  - Context-to-scorecard transformer
  - Competency generator
  - Scoring criteria generator
  - Weight distribution engine
  - Threshold suggestion engine
  - Round-specific scorecard generator
  - Variant generator
  - Refinement layer
  - Validation layer
  - Review / approval layer
  - Version / snapshot engine
  - Explainability layer
  - Mapping layer

Architecture layers:

- context layer
- competency layer
- criteria layer
- scoring layer
- variant layer
- validation layer
- review layer
- publish layer
- audit layer

Pipeline:

1. Consume structured builder context from AI Builder Foundation or Wizard.
2. Resolve scorecard type, evaluation mode, and target use case.
3. Generate competency framework and scoring dimensions.
4. Generate criteria, weight distribution, rubric guidance, and threshold model.
5. Optionally generate round-level scorecards or multi-round framework variants.
6. Validate scoring logic, thresholds, bindings, and tenant policy.
7. Hand off for review, approval, and publish.
8. Publish versioned scorecard to scorecard registry and downstream consumers.

Generation rules:

- Draft-first only
- Supports:
  - single-round scorecards
  - multi-round scorecard frameworks
  - global scorecards
  - round-specific scorecards
- Existing scorecards can be used as seeds for refinement and adaptation
- Tenant defaults and standards influence competency models, scoring rigor, and threshold recommendations

Compatibility model:

- Generated scorecards must map cleanly to execution engines
- Round-level scorecards can bind to template steps or flow steps
- Global scorecards can aggregate across multiple rounds

## 2. Database Design

Primary entities:

- `ai_scorecard_generation_session`
- `ai_scorecard_generation_run`
- `ai_scorecard_artifact_draft`
- `ai_scorecard_competency_record`
- `ai_scorecard_weight_record`
- `ai_scorecard_threshold_record`
- `ai_scorecard_variant_record`
- `ai_scorecard_validation_log`
- `ai_scorecard_review_record`
- `ai_scorecard_publish_record`
- `ai_scorecard_version_snapshot`
- `ai_scorecard_explainability_record`
- `ai_scorecard_audit_log`

Key fields:

- `tenant_id`
- `builder_project_id`
- `builder_session_id`
- `scorecard_type`
- `role_family`
- `job_function`
- `seniority_level`
- `status`
- `input_context_payload`
- `generated_scorecard_payload`
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
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

Entity purposes:

- `ai_scorecard_generation_session`: root generation session
- `ai_scorecard_generation_run`: each generation/regeneration run
- `ai_scorecard_artifact_draft`: structured draft scorecard payload
- `ai_scorecard_competency_record`: generated competency and rubric items
- `ai_scorecard_weight_record`: weight allocation data
- `ai_scorecard_threshold_record`: thresholds, pass/fail, cutoff logic
- `ai_scorecard_variant_record`: variant family and overrides
- `ai_scorecard_validation_log`: schema and scoring validation outcomes
- `ai_scorecard_review_record`: review and approval workflow
- `ai_scorecard_publish_record`: publish action records
- `ai_scorecard_version_snapshot`: immutable version snapshots
- `ai_scorecard_explainability_record`: rationale and explanation artifacts
- `ai_scorecard_audit_log`: end-to-end audit trail

## 3. API Structure

Generation APIs:

- Create scorecard session
- Generate scorecard draft
- Regenerate competency
- Regenerate weights
- Refine scorecard
- Fetch generated scorecard
- Generate variants
- Compare variants
- Fetch explainability summary

Validation APIs:

- Validate scorecard
- Validate engine compatibility
- Validate template compatibility
- Validate flow compatibility
- Validate thresholds
- Fetch validation issues
- Mark validation resolved

Review / publish APIs:

- Approve scorecard
- Reject / request revision
- Publish scorecard
- Rollback scorecard
- Deactivate scorecard if needed
- Fetch history

Rules:

- Draft and published states remain separate.
- Only draft scorecards are editable.
- Publish requires validation success and required approval gates.
- Regenerating one competency or weights creates new draft lineage.

## 4. UI Architecture

UI includes:

- Scorecard generator screen
- Competency list editor
- Weight distribution UI
- Threshold editor
- Preview scorecard
- Validation panel
- Review panel
- Version history
- Publish UI

Key modes:

1. Generate New Scorecard
2. Refine Existing Scorecard
3. Create Variant
4. Validate and Publish

UI rules:

- enterprise structured editor
- AI-generated items clearly marked
- strong separation of draft vs live scorecard
- validation visible before publish
- editable competency, weight, and threshold blocks

## 5. Execution Flow

1. User inputs context.
2. AI generates competencies.
3. AI generates scoring logic, weights, and thresholds.
4. User refines scorecard.
5. Validation runs.
6. Review and approval happen if required.
7. Scorecard publishes.
8. Mapping to flow, templates, and execution engines completes.

Supported flows:

- first-time generation flow
- refine existing scorecard flow
- generate variant flow
- reject / revise flow
- publish flow
- rollback flow

## 6. Edge Cases

- Conflicting weights
- Missing competencies
- Threshold mismatch
- Multi-round mismatch
- Template mismatch
- Stale draft
- Version conflict
- Engine compatibility failure
- Reviewer approves older draft instead of latest

Handling rules:

- Weight totals outside policy bounds block publish.
- Missing mandatory competencies trigger validation failure.
- Multi-round mismatch blocks mapping until resolved.
- Stale drafts require refresh or revalidation before publish.

## 7. Enterprise Features

- Draft-first structured scorecard generation
- Competency, rubric, weight, and threshold generation
- Round-level and global scorecard support
- Multi-round framework support
- Variant generation by role, seniority, and rigor
- Execution engine, template, and flow compatibility validation
- Explainability and rationale capture
- Controlled publish and rollback
- Full versioning and auditability
- Reusable architecture for future advanced scorecard intelligence

## 8. Integration Mapping

- `AI Builder Foundation`
- `Template Engine`
- `Flow Engine`
- `Execution Engines`
- `Analytics Engine`
- `Automation Engine`

