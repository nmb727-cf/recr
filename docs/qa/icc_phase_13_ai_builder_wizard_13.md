# Phase 13: AI Builder Wizard Experience

Prompt ID: `ICC-AI-BUILDER-WIZARD-13`  
Phase: `Interview Command Center / AI Builder / Phase 13`  
Module: `AI Builder Wizard Experience`

## Scope

Guided AI-assisted wizard layer on top of AI Builder Foundation for creating:

- interview templates
- round configurations
- question sets
- scorecards
- execution engine recommendations
- interview journeys / composite flows
- thresholds and evaluation logic
- anti-cheat recommendations
- panel / assessor setup suggestions
- full interview pack drafts

Candidate has no access. Wizard is tenant-scoped authoring UX for company and agency workspaces.

## 1. System Architecture

- Shared layer: `AIBuilderWizardLayer`
- Core components:
  - Wizard launchpad
  - Intent capture step
  - Role / JD / skills context step
  - Interview objective step
  - Interview structure step
  - Engine recommendation step
  - Question / scorecard draft step
  - Review / refine step
  - Validation step
  - Approval / publish step
  - Version / save draft step
  - Explainability / rationale panel
  - Collaboration / review routing step
  - Final mapping / activation step

Architecture layers:

- wizard state layer
- input capture layer
- context transformation layer
- generation trigger layer
- preview layer
- refinement layer
- validation layer
- approval layer
- publish handoff layer

Wizard-to-foundation relationship:

- Wizard captures and shapes inputs.
- AI Builder Foundation owns:
  - builder sessions
  - prompt orchestration
  - draft artifacts
  - validation framework
  - versioning
  - publish and audit records
- Wizard is the guided orchestration UX above the foundation, not a separate generation backend.

Generation timing model:

- AI generation is step-aware, not only once.
- Supports:
  - progressive recommendations during earlier steps
  - checkpoint generation after sufficient context
  - full draft generation
  - section-only regeneration
- Progressive enrichment is allowed, but publishability requires validation-complete state.

Wizard state model:

- step-based navigation
- draft save after each step
- resumable current step and context state
- artifact-type-aware dynamic pathing
- separate preview state from published state

Company and agency safety:

- same wizard framework
- tenant-specific defaults, review routing, and policies
- agency-specific delivery style and company-specific standards supported through context defaults

## 2. Database Design

Primary entities:

- `ai_builder_wizard_session`
- `ai_builder_wizard_step_state`
- `ai_builder_wizard_input_snapshot`
- `ai_builder_wizard_generation_checkpoint`
- `ai_builder_wizard_preview_record`
- `ai_builder_wizard_refinement_record`
- `ai_builder_wizard_validation_checkpoint`
- `ai_builder_wizard_review_route`
- `ai_builder_wizard_publish_handoff`
- `ai_builder_wizard_resume_state`
- `ai_builder_wizard_explainability_record`
- `ai_builder_wizard_audit_log`

Key fields:

- `tenant_id`
- `builder_project_id`
- `builder_session_id`
- `wizard_type`
- `current_step`
- `step_status`
- `draft_status`
- `generation_status`
- `validation_status`
- `review_status`
- `approval_status`
- `publish_status`
- `input_payload`
- `context_payload`
- `preview_payload`
- `explainability_payload`
- `resume_token`
- `started_at`
- `last_seen_at`
- `completed_at`
- `created_by`
- `updated_by`

Entity purposes:

- `ai_builder_wizard_session`: root wizard run
- `ai_builder_wizard_step_state`: per-step lifecycle and progress
- `ai_builder_wizard_input_snapshot`: frozen inputs by step or checkpoint
- `ai_builder_wizard_generation_checkpoint`: AI generation milestones
- `ai_builder_wizard_preview_record`: structured preview outputs shown to user
- `ai_builder_wizard_refinement_record`: manual edits and selective regeneration history
- `ai_builder_wizard_validation_checkpoint`: step and cross-step validation results
- `ai_builder_wizard_review_route`: reviewer assignment and approval routing
- `ai_builder_wizard_publish_handoff`: publish-ready handoff to foundation publish engine
- `ai_builder_wizard_resume_state`: resumable navigation and draft state
- `ai_builder_wizard_explainability_record`: rationale/confidence/explanation snapshots
- `ai_builder_wizard_audit_log`: full wizard activity trail

## 3. API Structure

**Wizard APIs**

- Create wizard session
- Fetch wizard session
- Save step input
- Fetch step state
- Move to next step
- Move to previous step
- Generate draft at step
- Regenerate selected section
- Fetch preview
- Save refinements
- Validate current wizard state
- Route for review
- Approve wizard outcome
- Publish through wizard
- Save as draft
- Resume wizard
- Cancel wizard
- Fetch explainability
- Fetch wizard audit trail

Responsibilities:

- Wizard APIs manage guided UX state, previews, step flow, and publish handoff.
- Builder Foundation APIs manage core draft artifacts, versioning, mapping, and publish records.

**Builder integration APIs**

- Transform wizard inputs to builder context
- Create/update builder session from wizard
- Sync draft artifact to wizard preview
- Map wizard output to template / flow / scorecard / question set

**Reviewer APIs**

- Fetch pending wizard reviews
- Add review comments
- Request revisions
- Approve/reject wizard output
- Compare wizard versions

Rules:

- Draft and published states stay separate.
- Publish is blocked if validation or approval gates fail.
- Section regeneration must create new preview/version lineage instead of silently mutating approved content.

## 4. UI Architecture

Wizard UI includes:

- Builder launchpad
- Artifact selection screen
- Guided multi-step wizard shell
- Left step navigation
- Main step workspace
- Right explainability / recommendation panel
- Draft preview area
- Validation banner / checklist
- Reviewer comments drawer
- Save draft / resume controls
- Publish confirmation flow
- Version compare view

Core step examples:

1. What are you creating?
- interview template
- question set
- scorecard
- composite flow
- full interview pack

2. Context intake
- role title
- job description
- experience level
- function / department
- skills
- location if relevant
- hiring goals

3. Interview objective
- screening
- technical depth
- communication
- leadership
- culture / behavior
- final evaluation
- custom objective

4. Structure preferences
- number of rounds
- desired engines
- duration preference
- async vs live mix
- anti-cheat strictness
- reviewer complexity

5. AI generation preview
- recommendations
- structured draft
- alternatives
- rationale

6. Review and refine
- edit sections
- regenerate one block
- change thresholds
- swap engine
- edit scorecard

7. Validate
- missing field checks
- compatibility checks
- publish readiness

8. Approval / publish
- assign reviewer
- publish now if allowed
- save as draft
- schedule later refinement

UI rules:

- wizard-based
- enterprise clean layout
- guided, not overwhelming
- explainable AI
- editable structured outputs
- strong draft/save/resume model
- no black-box publish behavior

## 5. Execution Flow

1. User launches AI Builder Wizard.
2. User selects artifact type or interview pack type.
3. Wizard captures structured inputs across guided steps.
4. Wizard transforms inputs into builder context.
5. AI generation runs at configured checkpoints.
6. Wizard shows structured previews and recommendations.
7. User refines sections manually or through selective regeneration.
8. Wizard validates current draft and linked artifacts.
9. Reviewer approval happens if policy requires it.
10. Wizard publishes or saves draft.
11. Published artifacts map into Interview Command Center through builder foundation.
12. Version history and audit trail remain preserved.
13. User can reopen later and continue through versioned workflow.

Supported flows:

- first-time creation flow
- save and resume flow
- revision flow
- approval flow
- reject and rework flow
- publish flow
- multi-artifact creation flow
- validation failure flow

## 6. Edge Cases

- User leaves wizard mid-step
- Incomplete JD
- Conflicting wizard choices
- AI output too generic
- Regeneration breaks prior valid section
- One artifact validates but linked artifact fails
- Reviewer comments arrive after new edits
- Publish attempted with stale preview
- Version conflict on resume
- User changes artifact type mid-wizard
- Tenant policy changes while draft is in progress
- Reviewer approves older version instead of latest

Handling rules:

- Mid-step exits persist partial save and resume token.
- Incomplete context triggers warnings and lower-confidence preview, not silent publishability.
- Stale preview blocks publish until regenerated or revalidated.
- Older-version approval is invalid if a newer unresolved draft exists.

## 7. Enterprise Features

- Guided entry point on top of AI Builder Foundation
- Progressive context capture with artifact-specific dynamic paths
- Step-level and full-draft generation support
- Section-only regeneration
- Multi-artifact pack creation support
- Draft-first, resumable workflow
- Explainability and rationale surfaced in-context
- Step-level and cross-step validation
- Approval routing and reviewer collaboration
- Clear separation between draft preview and active published configuration
- Tenant-safe company and agency defaults
- Reusable wizard architecture for future advanced AI Builder phases

## 8. Integration Mapping

- `AI Builder Foundation`
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
- `Notification Engine`

