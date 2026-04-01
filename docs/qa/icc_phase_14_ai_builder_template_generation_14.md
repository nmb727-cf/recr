# Phase 14: AI Builder Template Generation Engine

Prompt ID: `ICC-AI-BUILDER-TEMPLATE-GENERATION-14`  
Phase: `Interview Command Center / AI Builder / Phase 14`  
Module: `AI Builder Template Generation Engine`

## Scope

Tenant-scoped structured template generation engine for creating reusable draft artifacts for:

- interview templates
- round templates
- execution-engine-specific templates
- question set templates
- scorecard-ready template structures
- anti-cheat template suggestions
- panel setup template suggestions
- role / level / function variants

Candidate has no access. Output is always structured template artifacts, never free-text-only suggestions.

## 1. System Architecture

- Shared engine: `AITemplateGenerationEngine`
- Core components:
  - Template generation engine
  - Context-to-template transformer
  - Template schema resolver
  - Execution engine mapping layer
  - Question structure generator
  - Round structure generator
  - Scorecard hook generator
  - Threshold / rule suggestion engine
  - Template variant generator
  - Refinement / regeneration layer
  - Validation / compatibility layer
  - Review / approval handoff layer
  - Version / snapshot engine
  - Explainability / audit layer

Architecture layers:

- context intake layer
- artifact resolution layer
- schema layer
- generation layer
- variant layer
- validation layer
- review layer
- publish layer
- audit layer

Pipeline:

1. Consume structured builder context from AI Builder Foundation or Wizard.
2. Resolve target template type and target execution engine type.
3. Select schema backbone and engine-specific field set.
4. Generate structured draft template payload.
5. Optionally generate template family variants.
6. Validate schema, mapping, scorecard, thresholds, and tenant policy.
7. Hand off for review, approval, and publish.
8. Publish versioned template to registry/template engine.

Generation rules:

- Draft-first only
- Supports one-template and multi-template generation
- Supports template family/variant model
- Uses tenant defaults and standards as generation constraints
- Existing templates can be used as seed context for refinement/adaptation

Mapping behavior:

- Templates map to execution engines through validated engine-specific schema bindings
- Templates map to scorecard and flow layers through structured hook fields
- Composite flow child templates use same generation engine with child-step schema selection

## 2. Database Design

Primary entities:

- `ai_template_generation_session`
- `ai_template_generation_run`
- `ai_template_artifact_draft`
- `ai_template_schema_mapping`
- `ai_template_engine_mapping`
- `ai_template_variant_record`
- `ai_template_validation_log`
- `ai_template_refinement_record`
- `ai_template_review_record`
- `ai_template_publish_record`
- `ai_template_version_snapshot`
- `ai_template_explainability_record`
- `ai_template_audit_log`

Key fields:

- `tenant_id`
- `builder_project_id`
- `builder_session_id`
- `template_type`
- `target_engine_type`
- `role_family`
- `job_function`
- `seniority_level`
- `status`
- `input_context_payload`
- `generated_template_payload`
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
- `confidence_payload`
- `explainability_payload`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

Entity purposes:

- `ai_template_generation_session`: root generation session
- `ai_template_generation_run`: each generation or regeneration execution
- `ai_template_artifact_draft`: structured template draft payload
- `ai_template_schema_mapping`: template-to-schema resolution record
- `ai_template_engine_mapping`: template-to-engine compatibility binding
- `ai_template_variant_record`: variant family members and overrides
- `ai_template_validation_log`: schema, policy, and compatibility validation results
- `ai_template_refinement_record`: manual edits and partial regenerations
- `ai_template_review_record`: review, approval, or rejection workflow
- `ai_template_publish_record`: publish action log
- `ai_template_version_snapshot`: immutable draft/published versions
- `ai_template_explainability_record`: rationale and confidence snapshots
- `ai_template_audit_log`: end-to-end audit trail

## 3. API Structure

**Generation APIs**

- Create template generation session
- Attach builder context
- Generate template draft
- Generate multiple template variants
- Regenerate selected section
- Refine template draft
- Clone template into new draft
- Adapt existing template for new role / level
- Fetch generated template
- Fetch template variants
- Compare variants
- Fetch explainability summary

**Validation APIs**

- Validate generated template
- Validate engine compatibility
- Validate scorecard compatibility
- Validate flow compatibility
- Fetch validation issues
- Mark validation resolved

**Review / publish APIs**

- Submit template for review
- Assign reviewer
- Add review comments
- Request revision
- Approve template draft
- Reject template draft
- Publish template
- Rollback template version
- Deactivate template if needed
- Fetch template history

**Mapping APIs**

- Map template to execution engine
- Map template to scorecard structure
- Map template to flow builder
- Fetch mapping status

Rules:

- Draft and published behaviors are separate.
- Only draft versions are mutable.
- Publish requires successful validation and required approvals.
- Older drafts cannot be approved over newer unresolved revisions without explicit controlled override.

## 4. UI Architecture

UI includes:

- Template generation launch screen
- Context summary panel
- Generated template preview shell
- Structured template editor
- Variant comparison view
- Explainability side panel
- Validation issue panel
- Engine mapping panel
- Scorecard linkage panel
- Review comments drawer
- Version history view
- Publish confirmation flow

Key modes:

1. Generate New Template
2. Refine Existing Template
3. Create Variant from Template
4. Compare Alternatives
5. Validate and Publish

UI rules:

- enterprise layout
- structured editable artifact view
- AI suggestion clearly marked
- strong separation of draft vs live template
- validation visible before publish
- no black-box activation

## 5. Execution Flow

1. User provides builder context or opens wizard result.
2. Template Generation Engine receives structured context.
3. Engine resolves target schema and target engine type.
4. AI generates structured draft template.
5. Variants are also generated if requested.
6. User previews and refines template.
7. Validation runs.
8. Review and approval happen if required.
9. Template publishes.
10. Published template becomes available in Interview Registry / Template Engine.
11. Execution engines and flow engine consume published template.
12. Version history and audit remain preserved.

Supported flows:

- first-time generation flow
- refine existing template flow
- generate variant flow
- reject / revise flow
- publish flow
- rollback flow
- invalid mapping flow

## 6. Edge Cases

- AI output misses mandatory engine fields
- AI chooses wrong execution engine type
- Variant generation produces inconsistent schema
- Existing template under review gets edited again
- Publish attempted on stale draft
- Tenant standards conflict with generated draft
- Scorecard linkage missing
- Execution engine mapping invalid
- User regenerates one section causing version conflict
- Rollback requested for template already in active use
- Generic template output for niche role
- Reviewer approves older draft instead of latest

Handling rules:

- Missing mandatory fields blocks publish and marks validation failure.
- Invalid engine mapping blocks publish and requires regeneration or manual correction.
- Active-use rollback creates controlled version fallback rather than destructive replacement.
- Low-quality generic output is warned or blocked based on tenant quality threshold policy.

## 7. Enterprise Features

- Draft-first structured template generation
- Common template schema backbone with engine-specific extensions
- Tenant-safe defaults and standards injection
- Role / level / function variant generation
- Template family and override model
- Partial regeneration and controlled refinement
- Engine, flow, and scorecard compatibility validation
- Explainability and rationale capture
- Controlled publish and rollback
- Full versioning and auditability
- Reusable architecture for future advanced template intelligence

## 8. Integration Mapping

- `AI Builder Foundation`
- `AI Builder Wizard`
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

