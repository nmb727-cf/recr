# Phase 12: AI Builder Foundation

Prompt ID: `ICC-AI-BUILDER-FOUNDATION-12`  
Phase: `Interview Command Center / Foundation / Phase 12`  
Module: `AI Builder Foundation`

## Scope

Tenant-scoped AI-assisted authoring foundation for:

- interview templates
- interview flows
- interview rounds
- question sets
- scorecards
- evaluation criteria
- execution engine configurations
- composite interview journeys

AI Builder is a recruiter, hiring team, and reviewer authoring layer. Candidate has no access.

## 1. System Architecture

- Shared foundation: `AIBuilderFoundation`
- Core components:
  - AI builder workspace
  - Intent capture layer
  - Context intake engine
  - Prompt orchestration layer
  - Structured draft generator
  - Recommendation engine
  - Builder review/edit layer
  - Validation/policy layer
  - Versioning/snapshot engine
  - Approval/publish engine
  - Execution mapping layer
  - Audit/explainability layer
  - Collaboration/reviewer layer
  - Recruiter productivity linkage

Architecture layers:

- intent layer
- context layer
- prompt layer
- generation layer
- structured output layer
- validation layer
- review layer
- publish layer
- audit layer

Operating model:

- AI output is always draft-first.
- AI Builder never auto-activates artifacts directly into production use.
- Drafts must pass validation and approval before publish where policy requires.
- Published artifacts become versioned system assets consumed by template, flow, scorecard, question, and execution mapping layers.
- Company and agency workspaces use the same builder framework with tenant-safe defaults, policies, and publishing boundaries.

## 2. Database Design

Primary entities:

- `ai_builder_project`
- `ai_builder_session`
- `ai_builder_context_snapshot`
- `ai_builder_prompt_run`
- `ai_builder_draft_artifact`
- `ai_builder_recommendation_record`
- `ai_builder_validation_log`
- `ai_builder_review_record`
- `ai_builder_publish_record`
- `ai_builder_version_snapshot`
- `ai_builder_execution_mapping`
- `ai_builder_audit_log`
- `ai_builder_collaboration_record`
- `ai_builder_result_summary`

Key fields:

- `tenant_id`
- `created_by`
- `updated_by`
- `builder_type`
- `target_artifact_type`
- `status`
- `intent_text`
- `context_payload`
- `prompt_version`
- `model_used`
- `generation_status`
- `validation_status`
- `review_status`
- `approval_status`
- `publish_status`
- `draft_version`
- `published_version`
- `source_type`
- `confidence_score`
- `explainability_payload`
- `mapping_status`
- `audit_flags`

Entity purposes:

- `ai_builder_project`: parent authoring workspace for a builder initiative
- `ai_builder_session`: active generation/edit session
- `ai_builder_context_snapshot`: frozen input context used for generation
- `ai_builder_prompt_run`: prompt execution metadata and outputs
- `ai_builder_draft_artifact`: structured draft output
- `ai_builder_recommendation_record`: AI suggestions and alternative recommendations
- `ai_builder_validation_log`: schema/policy/compatibility checks
- `ai_builder_review_record`: approval or rejection workflow state
- `ai_builder_publish_record`: publication actions and targets
- `ai_builder_version_snapshot`: draft/published version history
- `ai_builder_execution_mapping`: mapping to engines and downstream artifacts
- `ai_builder_audit_log`: full explainable action trail
- `ai_builder_collaboration_record`: reviewer comments and assignments
- `ai_builder_result_summary`: generation quality, status, and publish summary

## 3. API Structure

**Builder APIs**

- Create builder session
- Capture builder intent
- Attach context
- Generate draft
- Regenerate section
- Refine draft
- Request recommendations
- Validate draft
- Save manual edits
- Compare versions
- Approve draft
- Publish artifact
- Rollback to prior version
- Map artifact to execution engine
- Fetch builder history
- Fetch explainability summary

**Template / output APIs**

- Create interview template from builder
- Create flow template from builder
- Create scorecard from builder
- Create question set from builder
- Create composite journey from builder

**Reviewer / collaboration APIs**

- Assign reviewer
- Add review comments
- Request revisions
- Approve/reject builder draft
- Fetch collaboration history

Rules:

- Draft and published states remain separate.
- Only authorized roles can approve or publish.
- Regeneration can target full artifact or specific sections.
- Published assets are versioned and traceable to source draft and prompt runs.

## 4. UI Architecture

AI Builder UI includes:

- Builder home / launchpad
- Intent capture wizard
- Role / level / skill / JD input screen
- Builder context screen
- AI generation workspace
- Structured output preview
- Recommendations side panel
- Manual edit shell
- Validation panel
- Review / approval panel
- Version comparison screen
- Publish confirmation screen
- Builder audit / explainability view

Role behavior:

- Recruiter / HR / Hiring Team:
  - create draft
  - refine draft
  - request AI suggestions
  - save edits
- Reviewer / Admin / Interview Architect:
  - review
  - comment
  - approve
  - reject
  - publish
- Candidate:
  - no access

UI rules:

- wizard-based enterprise authoring flow
- clear separation between AI suggestion and active configuration
- structured editable outputs only
- no black-box publishing
- explainability visible at decision points

## 5. Execution Flow

1. Recruiter opens AI Builder.
2. Recruiter provides role, JD, intent, and context.
3. Builder converts raw input into structured context.
4. Prompt orchestration produces draft artifacts.
5. Validation checks schema, policy, and engine compatibility.
6. User reviews draft in structured preview.
7. User edits or regenerates selected sections.
8. Reviewer comments, approves, or rejects if required.
9. Draft is published into versioned system artifact.
10. Published artifact maps to template engine, flow engine, scorecard engine, question engine, or execution mappings.
11. Recruiter uses published artifact inside Interview Command Center.
12. Audit trail and version history remain preserved.

Special flows:

- first-time generation flow
- refinement flow
- rejection/revision flow
- publish flow
- rollback flow
- mapping failure flow
- incomplete context flow

## 6. Edge Cases

- Incomplete JD
- Conflicting recruiter inputs
- AI output missing mandatory fields
- Invalid engine mapping
- Scorecard and flow mismatch
- Template edited while under review
- Publish attempted without approval
- Version conflict
- Builder session interrupted
- Regenerate only one section
- Rollback after published artifact already in use
- Tenant admin policy override
- AI output too generic or low quality

Handling rules:

- Incomplete context produces draft with warnings, not silent publish.
- Invalid mappings block publish.
- Under-review edits create new revision or require review reset by policy.
- Published artifact rollback preserves audit and in-use dependency awareness.

## 7. Enterprise Features

- Draft-first, human-in-control AI authoring model
- Structured output only
- Tenant-scoped builder infrastructure
- Explainability and auditability by default
- Draft vs active version separation
- Approval and publish gates
- Execution mapping validation
- Version comparison and rollback
- Collaboration and reviewer workflow
- Company and agency workspace support with tenant-safe defaults
- Reusable base for future advanced AI Builder phases

## 8. Integration Mapping

- `Interview Registry`
- `Template Engine`
- `Flow Engine`
- `Scorecard Engine`
- `Question Engine`
- `Execution Engines`
- `Composite Flow Engine`
- `Analytics Engine`
- `Automation Engine`
- `Audit / Governance Layer`

