# Company Module Verification Report

**Status:** Phase 1 Audit
**Date:** 2026-04-07
**Author:** Senior ATS Architect + QA Auditor

## 1. Implemented

### Job Management
- **Job Creation & Editing**: Fully supported via `JobRequisitionListView` and `JobRequisitionDetailView`.
- **Job Approval Workflow**: Supported with `approval_chain` in the model and `JobRequisitionApproveView`/`RejectView`.
- **Confidential Jobs**: `is_confidential` flag exists in `JobRequisition` model.
- **Multiple Locations**: Supported via `JobLocation` model and `location_id` in requisition.
- **Job Cloning**: `JobRequisitionCloneView` provides basic cloning functionality.

### Candidate Management
- **View Submissions**: Supported via `JobRequisitionCandidatesView` and pipeline views.
- **Candidate Profile**: Fully implemented in `apps/candidates`.
- **Candidate Notes & Tags**: Supported in models and views.
- **Candidate Ownership**: Tracked via `owner_user_id` and `owner_tenant_id`.
- **Deduplication**: Identity matching service exists in `apps/candidates/identity_service.py`.

### Pipeline Management
- **Kanban Pipeline**: Implemented in `PipelineBoard.tsx` using `react-beautiful-dnd`.
- **Drag & Drop**: Supported in the frontend and backed by stage transition APIs.
- **Custom Stages**: Supported via `JobStage` model and associated views.
- **Rejection Reasons**: Models include `rejection_reason` and `rejection_category`.

### Agency Management
- **Invite Agencies**: Supported via `AgencyRelationshipInviteView`.
- **Agency Empanelment**: Managed through `AgencyClientRelationship` with tiers and terms.
- **Job Distribution**: Supported via `is_published_to_agencies` and `AgencyJobAssignmentListView`.
- **Agency Submissions**: Implemented in `AgencySubmitCandidateView`.

### Interview Management
- **Interview Scheduling**: Supported via `InterviewManualSchedulingView`.
- **Panel Assignment**: Supported in models and `InterviewPanelSlotsView`.
- **Feedback Collection**: Supported via `InterviewFeedbackSubmit.tsx` and backend models.
- **Interview Templates**: Fully implemented in `apps/interviews`.

### Offer Management
- **Offer Generation**: `OfferLetter` model and creation API exist.
- **Offer Approval**: `OfferLetterApproveView` is implemented.
- **Offer Tracking**: Status tracking (draft, sent, accepted, etc.) is implemented in the model.

---

## 2. Partial

- **Job Cloning**: The current implementation performs a shallow clone of the requisition but does **not** clone associated `JobStage` records or `JobHiringTeamMember` records.
- **Bulk Stage Movement**: `BulkActionView` supports bulk status changes (shortlist/reject) but does not yet support moving multiple candidates across custom stages in a single action.
- **Offer Management UI**: While models and APIs exist, the UI for generating and tracking offers is fragmented across QuickView panels and lacks a dedicated management dashboard.

---

## 3. Missing

- **Job Expiry & Renewal**: While `target_date` exists, explicit logic for automatic expiry and a renewal workflow (extending dates/re-opening) is not prominently implemented.
- **Approval Hierarchy Depth**: Approval is supported, but a strictly enforced multi-level hierarchy (beyond a simple chain) with delegation logic is not fully verified.

---

## 4. Logic Issues

- **Ownership Conflict**: When an agency submits a candidate already in the system, the `identity_service` links the user but ownership rules (who gets credit/commission) rely on `AgencyClientRelationship.retention_days`, which requires careful enforcement during the submission flow.
- **Manual Tenant Filtering**: As noted in previous audits, multi-tenancy relies on manual `.filter(tenant_id=...)` in views, posing a leak risk if missed in new endpoints.

---

## 5. Architecture Issues

- **Offer Management Location**: Offer logic is split between `pipeline` (status), `jobs` (defaults), and `documents` (actual offer letter). This fragmentation can lead to synchronization issues.
- **Candidate Global vs. Private**: Candidates are global (`public` tenant), but their interactions with a company are private. This is handled via `CandidateWorkspace`, but ensuring `CandidateNote` and other private data never leaks in "Global Search" views is a high-complexity area.

---

## Summary Table

| Requirement | Status | Note |
|-------------|--------|------|
| Job Approval | ✅ | Functional chain |
| Kanban Pipeline| ✅ | Drag-drop active |
| Agency Submission| ✅ | Fully wired |
| Offer Tracking | ⚠️ | Backend ready, UI fragmented |
| Job Cloning | ⚠️ | Shallow clone only |
| Deduplication | ✅ | Multi-point matching |
| Custom Stages | ✅ | Per-job configuration |
| Tenant Isolation| ✅ | Manually enforced |
