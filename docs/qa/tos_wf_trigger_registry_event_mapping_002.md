# QA Document: Workflow Trigger Registry + Event Mapping
**PROMPT ID:** TOS-WF-TRIGGER-REGISTRY-EVENT-MAPPING-002  
**Module:** Workflow Trigger Registry + Event Mapping  
**Priority:** Critical  
**Date:** 2026-04-08

---

## 1. Overview

This module connects real system events to workflow execution. Before this layer, workflows existed in the UI but did not execute in response to any system activity. The trigger registry defines which events are valid, trigger mappings bind workflows to those events (with filters), and the event listener starts or advances workflow instances when events fire.

---

## 2. Key Components

### 2.1 Trigger Registry
- **Model:** `WorkflowEventDefinition` (canonical, in `orchestration_center`)
- **Table:** `icc_workflow_event_definitions`
- **Seeded via:** `python manage.py seed_trigger_registry`
- **Entries:** 39 standard events across Jobs, Candidates, Agency, Pipeline, Interview, Offer, Onboarding, Tasks, SLA, and Resume/advance events

### 2.2 Trigger Mapping
- **Model:** `WorkflowEventSubscription`
- **Table:** `icc_workflow_event_subscriptions`
- **Fields:** `workflow`, `event_definition`, `trigger_filters` (JSON), `is_active`, `tenant_id`
- **Filter operators:** `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `contains`, `not_contains`, `in`, `not_in` (via `key__op` suffix)

### 2.3 Event Listener
- **Service:** `apps/workflow_execution/services/workflow_event_listener.py`
- **Class:** `WorkflowEventListener`
- **Key methods:**
  - `receive_event()` — main entry point
  - `validate_registered_event()` — registry check
  - `find_matching_workflows()` — subscription + filter evaluation
  - `evaluate_trigger_filters()` — per-filter condition logic
  - `start_workflow_instances()` — creates `WorkflowInstance`
  - `log_event_match_result()` — writes `WorkflowEventDebugTrace`

### 2.4 Event Logging
- **Model:** `WorkflowEventLog` — one record per emitted event (status: `emitted` → `consumed` / `ignored`)
- **Model:** `WorkflowEventDebugTrace` — one record per workflow match decision (`matched`, `filtered_out`, `inactive`, `started`, `failed`, `invalid`)

### 2.5 Real Signal Connections (15 wired)
- **File:** `apps/workflow_execution/signals.py`
- **Loaded in:** `apps/workflow_execution/apps.py` → `ready()`
- **Events wired:** `job_created`, `job_approved`, `job_published`, `candidate_applied`, `stage_changed`, `candidate_shortlisted`, `candidate_rejected`, `agency_submission_created`, `interview_completed`, `interview_feedback_submitted`, `interview_scheduled`, `offer_accepted`, `offer_rejected`, `onboarding_completed`

### 2.6 Wait / Resume Event Mapping

| Wait Reason | Resume Events |
|------------|---------------|
| `waiting_approval` | `approval_received` |
| `waiting_candidate` | `candidate_response_received`, `offer_accepted`, `offer_rejected` |
| `waiting_client` | `client_feedback_received` |
| `waiting_recruiter` | `recruiter_review_completed`, `interview_feedback_submitted` |
| `waiting_scheduler` | `interview_scheduled` |
| `waiting_signature` | `document_signed` |

---

## 3. Database Models Modified

| Model | Change |
|-------|--------|
| `WorkflowInstance` | Added `wait_reason` field (migration 0002) |
| `WorkflowStageExecution` | Added `wait_reason` field (migration 0002) |

---

## 4. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/workflow/triggers/registry/` | List all registered trigger events |
| `GET` | `/api/v1/workflow/triggers/registry/{id}/` | Detail for one event definition |
| `GET` | `/api/v1/workflow/triggers/mappings/` | List tenant trigger-to-workflow mappings |
| `POST` | `/api/v1/workflow/triggers/mappings/` | Create a mapping |
| `PUT/PATCH` | `/api/v1/workflow/triggers/mappings/{id}/` | Update a mapping |
| `DELETE` | `/api/v1/workflow/triggers/mappings/{id}/` | Remove a mapping |
| `GET` | `/api/v1/workflow/events/logs/` | List emitted event logs |
| `GET` | `/api/v1/workflow/events/logs/{id}/` | Detail for one event log |
| `GET` | `/api/v1/workflow/events/logs/{id}/traces/` | Debug traces for a log entry |
| `GET` | `/api/v1/workflow/events/traces/` | List all debug traces |
| `POST` | `/api/v1/workflow/events/test-emit/` | Fire a test event through the full pipeline |

---

## 5. Test Cases

| ID | Test Case | File | Expected Result | Status |
|----|-----------|------|-----------------|--------|
| TREG-01 | `job_created` event starts matching workflow | `test_execution_engine.py::TestJobCreatedStartsWorkflow` | `WorkflowInstance` created, status `waiting`, `EventLog.status = consumed` | ✅ PASS |
| TREG-02 | `candidate_applied` with `source=direct` mismatches `source=agency` filter | `test_execution_engine.py::TestCandidateAppliedFilterMismatch::test_non_agency_source_is_filtered_out` | No instance created; trace decision = `filtered_out`; log status = `ignored` | ✅ PASS |
| TREG-03 | `candidate_applied` with `source=agency` matches filter | `test_execution_engine.py::TestCandidateAppliedFilterMismatch::test_agency_source_is_matched` | Instance created; log status = `consumed` | ✅ PASS |
| TREG-04 | `agency_submission_created` starts agency workflow | `test_execution_engine.py::TestAgencySubmissionStartsWorkflow` | Instance created with correct `entity_type = agency_submission` | ✅ PASS |
| TREG-05 | `approval_received` resumes waiting instance | `test_execution_engine.py::TestApprovalReceivedResumesWorkflow` | Instance advances to `completed`; timeline has `Workflow resumed` | ✅ PASS |
| TREG-06 | Unknown event key emitted | `test_execution_engine.py::TestInvalidEventKeyIsRejected` | `EventLog.status = ignored`; no instances created | ✅ PASS |
| TREG-07 | `score__gt` filter passes | `TestTriggerFilterEvaluation::test_gt_filter_passes` | Returns `True` | ✅ PASS |
| TREG-08 | `score__gt` filter fails | `TestTriggerFilterEvaluation::test_gt_filter_fails` | Returns `False` | ✅ PASS |
| TREG-09 | `title__contains` filter | `TestTriggerFilterEvaluation::test_contains_filter` | Returns `True` | ✅ PASS |
| TREG-10 | Empty filter always matches | `TestTriggerFilterEvaluation::test_no_filters_always_matches` | Returns `True` | ✅ PASS |

**Total: 12 tests, 12 passed.**

---

## 6. Files Created / Modified

| File | Type |
|------|------|
| `apps/workflow_execution/services/workflow_event_listener.py` | Modified (full rewrite) |
| `apps/workflow_execution/signals.py` | Created |
| `apps/workflow_execution/apps.py` | Modified |
| `apps/workflow_execution/models/execution.py` | Modified (wait_reason fields) |
| `apps/workflow_execution/models/__init__.py` | Modified |
| `apps/workflow_execution/migrations/0002_add_wait_reason.py` | Created |
| `apps/workflow_execution/api/serializers.py` | Modified |
| `apps/workflow_execution/api/views.py` | Modified |
| `apps/workflow_execution/urls.py` | Modified |
| `apps/workflow_execution/management/commands/seed_trigger_registry.py` | Created |
| `apps/workflow_execution/tests/test_execution_engine.py` | Modified |

---

## 7. Manual QA Checklist

- [ ] Run `python manage.py seed_trigger_registry` — confirm 39 events seeded without errors
- [ ] `GET /api/v1/workflow/triggers/registry/?active=true` — confirm all 39 events returned
- [ ] Create a workflow in the UI set to trigger on `job_created`
- [ ] Create a mapping: `POST /api/v1/workflow/triggers/mappings/` with workflow + `job_created` event
- [ ] Fire `POST /api/v1/workflow/events/test-emit/` with `event_key=job_created` — confirm `EventLog.status=consumed`
- [ ] Fire same test-emit with an unregistered key — confirm `EventLog.status=ignored`
- [ ] Add a filter `{"source": "agency"}` to a mapping — fire with `source=direct` — confirm `filtered_out` trace
- [ ] Check `GET /api/v1/workflow/events/logs/{id}/traces/` for decision detail

---

## 8. Known Constraints

- Trigger registry entries must be seeded before any workflow subscriptions can reference them
- Resume events (`approval_received` etc.) do not start new workflows — they only advance waiting instances
- Filter evaluation is AND-based for top-level keys; OR logic requires the `__op` suffix approach
