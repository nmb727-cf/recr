# Phase 18: AI Builder Publish & Governance Layer

Prompt ID: `ICC-AI-BUILDER-PUBLISH-GOVERNANCE-18`  
Phase: `Interview Command Center / AI Builder / Phase 18`  
Module: `AI Builder Publish & Governance Layer`

## Scope

Tenant-scoped publish and governance control layer for moving AI-generated artifacts from draft to approved to published to active use.

Governed artifact types:

- templates
- flows
- scorecards
- automations
- multi-artifact interview packs

Candidate has no access. This layer is operational control infrastructure for reviewers, approvers, governance owners, QA, and tenant admins.

## 1. System Architecture

- Shared layer: `AIPublishGovernanceLayer`
- Core components:
  - Publish control engine
  - Approval workflow engine
  - Policy enforcement engine
  - Validation gate engine
  - Version governance engine
  - Activation / deactivation control
  - Safe rollback engine
  - Artifact dependency checker
  - Multi-artifact publish coordinator
  - Explainability / evidence viewer
  - Audit and change log engine
  - Exception / override control
  - Tenant governance settings layer
  - Compliance / review routing layer

Architecture layers:

- artifact intake layer
- validation gate layer
- policy layer
- approval layer
- publish layer
- activation layer
- dependency layer
- rollback layer
- audit layer

Artifact lifecycle model:

- `draft`
- `under_validation`
- `validation_failed`
- `awaiting_review`
- `awaiting_approval`
- `approved`
- `publish_pending`
- `published`
- `active`
- `inactive`
- `superseded`
- `rollback_pending`
- `rolled_back`
- `rejected`
- `cancelled`
- `retired`

Governance flow:

1. Draft artifact enters governance intake.
2. Validation and policy checks run.
3. Dependency and impact checks run.
4. Approval route is resolved by tenant policy and artifact type.
5. Reviewers and approvers act on evidence, explainability, and readiness.
6. Publish creates immutable versioned record.
7. Activation is immediate, scheduled, or deferred.
8. Supersede, deactivate, or rollback is handled through controlled governance actions.

Role model:

- creator/requester
- reviewer
- approver
- publisher
- governance admin
- tenant admin
- override authority

Rules:

- no direct AI draft to live activation
- validation before publish is mandatory
- approval is explicit and policy-driven
- dependency and impact checks run before activation
- active production configs are protected from unsafe replacement
- company and agency tenants can have different approval strictness, but the same governance framework

## 2. Database Design

Primary entities:

- `ai_publish_request`
- `ai_publish_artifact_record`
- `ai_publish_dependency_check`
- `ai_publish_validation_gate`
- `ai_publish_approval_route`
- `ai_publish_approval_action`
- `ai_publish_policy_evaluation`
- `ai_publish_version_record`
- `ai_publish_activation_record`
- `ai_publish_rollback_record`
- `ai_publish_override_record`
- `ai_publish_bundle_record`
- `ai_publish_explainability_snapshot`
- `ai_publish_audit_log`
- `ai_governance_policy`
- `ai_governance_role_matrix`
- `ai_governance_exception_record`

Key fields:

- `tenant_id`
- `artifact_type`
- `artifact_id`
- `artifact_version_id`
- `draft_version`
- `published_version`
- `requested_by`
- `reviewed_by`
- `approved_by`
- `published_by`
- `status`
- `validation_status`
- `policy_status`
- `approval_status`
- `activation_status`
- `rollback_status`
- `dependency_status`
- `override_status`
- `bundle_id`
- `effective_from`
- `effective_to`
- `superseded_by`
- `reason_code`
- `approval_notes`
- `policy_payload`
- `audit_payload`
- `created_at`
- `updated_at`

Entity purposes:

- `ai_publish_request`: root publish workflow object
- `ai_publish_artifact_record`: artifact and version binding for request
- `ai_publish_dependency_check`: compatibility and dependency graph outcomes
- `ai_publish_validation_gate`: validation gate results
- `ai_publish_approval_route`: resolved approval workflow
- `ai_publish_approval_action`: individual reviewer/approver actions
- `ai_publish_policy_evaluation`: tenant policy evaluation output
- `ai_publish_version_record`: immutable published version record
- `ai_publish_activation_record`: activation/deactivation scheduling and state
- `ai_publish_rollback_record`: rollback request and execution state
- `ai_publish_override_record`: controlled override actions
- `ai_publish_bundle_record`: multi-artifact publish bundle
- `ai_publish_explainability_snapshot`: explainability and evidence snapshot at decision time
- `ai_publish_audit_log`: complete governance action log
- `ai_governance_policy`: tenant-specific governance settings
- `ai_governance_role_matrix`: maker-checker and approver permissions
- `ai_governance_exception_record`: exception/waiver requests and outcomes

## 3. API Structure

**Publish APIs**

- Create publish request
- Attach artifact to publish request
- Create bundle publish request
- Run dependency check
- Run publish readiness check
- Fetch publish readiness summary
- Submit for approval
- Approve publish request
- Reject publish request
- Request revision
- Publish artifact
- Activate published version
- Deactivate active version
- Supersede version
- Rollback version
- Cancel publish request
- Fetch publish history

**Governance APIs**

- Create governance policy
- Update governance policy
- Fetch governance policy
- Evaluate artifact against policy
- Define role approval matrix
- Fetch approval route
- Add exception / override request
- Approve override
- Reject override
- Fetch explainability evidence
- Fetch validation evidence
- Fetch audit trail

**Bundle / dependency APIs**

- Validate multi-artifact bundle
- Check artifact compatibility
- Check template-flow-scorecard-automation linkage
- Fetch dependency graph
- Block publish on missing dependency
- Simulate publish impact

Rules:

- Draft and published states remain separate.
- Single artifact and bundle workflows use same governance engine with bundle-aware dependency rules.
- Publish is blocked if readiness, approval, or dependency checks fail.
- Overrides cannot bypass hard dependency invalidation unless tenant policy explicitly supports controlled exception mode.

## 4. UI Architecture

UI includes:

- Publish queue dashboard
- Artifact publish request screen
- Multi-artifact bundle publish screen
- Publish readiness checklist
- Validation evidence panel
- Policy evaluation panel
- Approval route panel
- Reviewer / approver action drawer
- Dependency graph / impact panel
- Version history view
- Activation / deactivation controls
- Rollback confirmation flow
- Override / exception request screen
- Audit trail view
- Explainability / rationale side panel

Key UI modes:

1. Submit for Publish
2. Review Readiness
3. Approve / Reject
4. Activate / Supersede
5. Rollback / Recover
6. Override / Exception Handling
7. Audit & Governance Review

UI rules:

- enterprise layout
- no black-box publish behavior
- readiness and risk clearly visible
- draft vs active version always clear
- approvals explicit
- rollback impact visible before execution

## 5. Execution Flow

1. Draft artifact is generated by AI Builder.
2. Validation completes.
3. User submits artifact for publish.
4. Governance layer checks readiness, policy, dependency, and approval route.
5. Reviewer / approver reviews evidence.
6. Approval, revision, or rejection occurs.
7. Approved artifact publishes as versioned record.
8. Artifact activates immediately or on schedule if allowed.
9. Downstream systems consume published version.
10. Audit trail records all actions.
11. If an issue is found later, rollback, supersede, or deactivate flow is used.

Supported flows:

- first-time publish flow
- re-publish updated version flow
- multi-artifact bundle publish flow
- approval rejection flow
- revision and resubmit flow
- rollback flow
- override / exception flow
- publish with future effective date flow

## 6. Edge Cases

- Publish attempted without required approval
- Artifact validation passed earlier but dependency changed later
- Reviewer approves stale draft version
- Policy changed while publish request is pending
- Linked artifact unpublished during bundle review
- Rollback requested on artifact currently in live use
- Override granted but dependency still invalid
- Simultaneous publish requests for same artifact
- Supersede requested while prior activation still pending
- One artifact in bundle passes and another fails
- Approver unavailable / SLA breach
- Tenant admin changes approval matrix mid-process

Handling rules:

- Stale approvals are invalid if draft lineage changed.
- Dependency re-check runs at final publish boundary, not only at request creation.
- Live-use rollback requires impact analysis and may prefer corrective forward version over direct rollback.
- Bundle publish is atomic by default unless tenant policy explicitly supports partial staged activation.

## 7. Enterprise Features

- Draft-first governance barrier between AI output and production activation
- Artifact lifecycle governance across validation, approval, publish, activation, supersede, and rollback
- Maker-checker and multi-approver support
- Tenant-specific governance policies
- Artifact-type-specific governance strictness
- Dependency and impact simulation
- Single artifact and bundle publish coordination
- Explainability and validation evidence visibility
- Controlled override and exception handling
- Safe rollback with approval and dependency awareness
- Full auditability and change management history
- Reusable governance framework for future AI Builder growth

## 8. Integration Mapping

- `AI Builder Foundation`
- `AI Builder Wizard`
- `Template Generation Engine`
- `Flow Generation Engine`
- `Scorecard Generation Engine`
- `Automation Generation Engine`
- `Interview Registry`
- `Template Engine`
- `Flow Engine`
- `Scorecard Engine`
- `Automation Engine`
- `Composite Flow Engine`
- `Execution Engines`
- `Analytics Engine`
- `Audit / Governance Layer`
- `Notification Engine`

