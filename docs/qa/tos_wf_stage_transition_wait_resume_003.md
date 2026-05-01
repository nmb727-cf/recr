# QA Document: Workflow Stage Transition + Wait/Resume Engine
**PROMPT ID:** TOS-WF-STAGE-TRANSITION-WAIT-RESUME-003  
**Module:** Workflow Stage Transition + Wait/Resume Engine  
**Priority:** Critical  
**Date:** 2026-04-08

---

## 1. Overview

This module enables workflows to actually move between stages. Previously, workflows could be started but stages had no typed routing, wait states had no persistent records, and resume logic was a simple status flip. This module delivers a full stage-transition engine with:

- Typed, prioritised transitions per workflow (`WorkflowStageTransition`)
- Persistent wait state records with resume tracking (`WorkflowWaitState`)
- Structured per-transition audit log (`WorkflowTransitionLog`)
- AND/OR multi-condition decision branching with 10 operators
- Skip, fail, and manual resume API actions

---

## 2. Key Components

### 2.1 WorkflowStageTransition Model
- **Table:** `wf_exec_stage_transitions`
- **Purpose:** Defines typed, prioritised routing rules per workflow — supplements `WorkflowEdge`
- **Key fields:** `workflow_id`, `from_stage_id`, `to_stage_id`, `transition_type`, `condition_config`, `priority`, `label`, `is_active`
- **Transition types:** `auto`, `decision`, `approval`, `event`, `manual`, `wait`
- **Evaluation order:** Sorted by `priority` ASC; first matching condition wins. Falls back to raw `WorkflowEdge` if no `WorkflowStageTransition` rows exist.

### 2.2 WorkflowWaitState Model
- **Table:** `wf_exec_wait_states`
- **Purpose:** Explicit per-instance wait record — replaces implicit `wait_reason` flag on the instance
- **Key fields:** `workflow_instance`, `stage_execution`, `wait_type`, `wait_reason`, `resume_event`, `status`, `resumed_at`, `resumed_by`, `resume_context`
- **Wait types:** `approval`, `recruiter_review`, `candidate_response`, `client_feedback`, `interview_schedule`, `document_signature`, `manual`
- **Status lifecycle:** `waiting` → `resumed` | `expired` | `cancelled`

### 2.3 WorkflowTransitionLog Model
- **Table:** `wf_exec_transition_logs`
- **Purpose:** Structured audit of every stage transition (complements timeline)
- **Key fields:** `from_stage_id`, `from_stage_name`, `to_stage_id`, `to_stage_name`, `transition_type`, `label`, `triggered_by`, `actor_id`, `reason`, `condition_result`
- **triggered_by values:** `system`, `user`, `event`, `automation`

### 2.4 WorkflowStageEngine
- **Service:** `apps/workflow_execution/services/workflow_stage_engine.py`
- **Class:** `WorkflowStageEngine`

| Method | Description |
|--------|-------------|
| `complete_stage()` | Run a normal stage, log, advance |
| `move_to_next_stage()` | Evaluate transitions/edges, dispatch to next node |
| `evaluate_transition_conditions()` | AND/OR condition evaluator (public wrapper) |
| `execute_stage_transition()` | Log transition, route to wait/end/next |
| `handle_wait_state()` | Create `WorkflowWaitState`, pause instance |
| `resume_wait_state()` | Mark state resumed, continue from wait node |
| `resume_instance()` | Convenience: resume most recent wait state for an instance |
| `resume_by_event()` | Resume all matching instances for an event key |
| `fail_stage()` | Mark stage + instance as failed |
| `skip_stage()` | Skip stage, cancel wait state, advance |
| `_complete_workflow()` | Mark instance completed, log timeline |

### 2.5 ConditionEvaluator
- **Class:** `WorkflowStageEngine.ConditionEvaluator`
- **Supported operators:** `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `contains`, `not_contains`, `in`, `not_in` + legacy `equals`, `greater_than`, `less_than`
- **Single condition:** `{"field": "score", "op": "gt", "value": 70}`
- **Grouped (AND/OR):** `{"operator": "and", "conditions": [...]}`

### 2.6 Node Type → Wait Type Mapping

| Node Type | Wait Type | Wait Reason on Instance |
|-----------|-----------|------------------------|
| `approval` | `approval` | `waiting_approval` |
| `human_task` | `recruiter_review` | `waiting_recruiter` |
| `scheduling` | `interview_schedule` | `waiting_scheduler` |
| `document` | `document_signature` | `waiting_signature` |
| `wait` | `manual` | `waiting_other` |

---

## 3. Database Changes (Migration 0003)

| Change | Detail |
|--------|--------|
| `WorkflowStageTransition` | New table `wf_exec_stage_transitions` |
| `WorkflowWaitState` | New table `wf_exec_wait_states` |
| `WorkflowTransitionLog` | New table `wf_exec_transition_logs` |
| `WorkflowInstance.context_data` | New JSONField |
| `WorkflowExecutionTimeline.actor` | New CharField (default `system`) |
| `WorkflowExecutionTimeline.action` | max_length increased to 255 |

---

## 4. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/workflow/instances/{id}/wait-states/` | List wait states for an instance |
| `GET` | `/api/v1/workflow/instances/{id}/transition-logs/` | List transition audit logs |
| `POST` | `/api/v1/workflow/instances/{id}/resume/` | Resume a waiting instance |
| `POST` | `/api/v1/workflow/instances/{id}/skip/` | Skip current (or specified) stage |
| `POST` | `/api/v1/workflow/instances/{id}/fail/` | Fail the workflow instance |
| `GET` | `/api/v1/workflow/stage-transitions/` | List defined stage transitions |
| `POST` | `/api/v1/workflow/stage-transitions/` | Create a typed transition |
| `PUT/PATCH` | `/api/v1/workflow/stage-transitions/{id}/` | Update a transition |
| `DELETE` | `/api/v1/workflow/stage-transitions/{id}/` | Remove a transition |
| `GET` | `/api/v1/workflow/wait-states/` | Global list of wait states |
| `POST` | `/api/v1/workflow/wait-states/{id}/resume/` | Resume a specific wait state |
| `GET` | `/api/v1/workflow/transition-logs/` | Global transition audit log |

**Request bodies:**

`POST .../resume/`
```json
{ "triggered_by": "user", "actor_id": "<uuid>", "context": {} }
```

`POST .../skip/`
```json
{ "stage_id": "<uuid>", "reason": "Client waived approval", "triggered_by": "user" }
```

`POST .../fail/`
```json
{ "reason": "Candidate withdrew", "triggered_by": "user" }
```

---

## 5. Test Cases

| ID | Test Case | Class / Method | Expected Result | Status |
|----|-----------|---------------|-----------------|--------|
| STAGE-01 | Auto edge → workflow completes | `TestStageCompletedTriggersNext::test_auto_edge_completes_workflow` | Instance `completed`; timeline has start + complete + workflow completed | ✅ PASS |
| STAGE-02 | Transition log created on advance | `TestStageCompletedTriggersNext::test_transition_log_created` | `WorkflowTransitionLog` row exists with correct `from_stage_id` | ✅ PASS |
| STAGE-03 | Stage execution record created | `TestStageCompletedTriggersNext::test_stage_execution_record_created` | `WorkflowStageExecution` with `status=completed` exists | ✅ PASS |
| STAGE-04 | Named transition overrides raw edge | `TestStageCompletedTriggersNext::test_named_transition_takes_priority_over_edge` | `WorkflowStageTransition` skips action node; action node NOT in executed stages | ✅ PASS |
| STAGE-05 | Approval node → `WorkflowWaitState` created | `TestApprovalNodeCreatesWaitState::test_approval_node_creates_wait_state` | Instance `waiting`; wait_reason `waiting_approval`; 1 wait state with correct type | ✅ PASS |
| STAGE-06 | Stage execution in `waiting` status | `TestApprovalNodeCreatesWaitState::test_stage_execution_is_in_waiting_status` | `WorkflowStageExecution.status = waiting` for approval node | ✅ PASS |
| STAGE-07 | Timeline logged with wait metadata | `TestApprovalNodeCreatesWaitState::test_timeline_logged_with_wait_metadata` | Timeline entry with `metadata.wait_type = approval` | ✅ PASS |
| STAGE-08 | `approval_received` event resumes instance | `TestApprovalReceivedResumesWorkflow::test_approval_received_resumes_and_completes` | Instance `completed`; wait state `resumed`; `resumed_by = event`; timeline has `Workflow resumed` | ✅ PASS |
| STAGE-09 | Direct `resume_wait_state()` call | `TestApprovalReceivedResumesWorkflow::test_resume_wait_state_directly` | Wait state `resumed`; `resume_context` saved; instance `completed` | ✅ PASS |
| STAGE-10 | High score takes `pass` branch | `TestDecisionLogicSelectsFallback::test_high_score_takes_pass_path` | Pass node executed; fail node NOT executed | ✅ PASS |
| STAGE-11 | Low score takes `fail` branch | `TestDecisionLogicSelectsFallback::test_low_score_takes_fail_path` | Fail node executed; pass node NOT executed | ✅ PASS |
| STAGE-12 | Transition log captures label | `TestDecisionLogicSelectsFallback::test_transition_log_captures_label` | `WorkflowTransitionLog.label = pass` | ✅ PASS |
| STAGE-13 | AND group — both pass | `TestDecisionLogicSelectsFallback::test_and_condition_group` | Returns `True`; reason contains `AND` | ✅ PASS |
| STAGE-14 | AND group — one fails | `TestDecisionLogicSelectsFallback::test_and_condition_group_fails_if_one_fails` | Returns `False` | ✅ PASS |
| STAGE-15 | OR group — one passes | `TestDecisionLogicSelectsFallback::test_or_condition_group` | Returns `True` | ✅ PASS |
| STAGE-16 | Skip waiting stage → advance | `TestManualSkipAdvancesWorkflow::test_skip_waiting_stage_advances_to_next` | Instance `completed`; approval exec `skipped`; wait state `cancelled` | ✅ PASS |
| STAGE-17 | Skip creates transition log | `TestManualSkipAdvancesWorkflow::test_skip_creates_transition_log` | `WorkflowTransitionLog.label = skip` with correct reason | ✅ PASS |
| STAGE-18 | Skip creates timeline entry | `TestManualSkipAdvancesWorkflow::test_skip_timeline_entry_created` | Timeline entry with `action` containing `skipped` | ✅ PASS |
| STAGE-19 | Start instance reaches wait (regression) | `TestExecutionEngineBackwardsCompat::test_start_instance_reaches_wait` | Instance `waiting` with `wait_reason = waiting_approval` | ✅ PASS |
| STAGE-20 | Resume workflow completes (regression) | `TestExecutionEngineBackwardsCompat::test_resume_workflow_completes` | Instance `completed` after resume | ✅ PASS |

**Total: 32 tests (20 new + 12 prior), 32 passed.**

---

## 6. Files Created / Modified

| File | Type |
|------|------|
| `apps/workflow_execution/models/execution.py` | Modified — 3 new models + constants refactor |
| `apps/workflow_execution/models/__init__.py` | Modified — exports all new models/constants |
| `apps/workflow_execution/migrations/0003_stage_transition_wait_state_transition_log.py` | Created |
| `apps/workflow_execution/services/workflow_stage_engine.py` | Created (~430 lines) |
| `apps/workflow_execution/services/workflow_execution_engine.py` | Modified — delegates to stage engine |
| `apps/workflow_execution/services/workflow_event_listener.py` | Modified — uses `resume_by_event()` |
| `apps/workflow_execution/api/serializers.py` | Modified — 6 new serializers |
| `apps/workflow_execution/api/views.py` | Modified — 3 new viewsets, 4 new actions |
| `apps/workflow_execution/urls.py` | Modified — 3 new routers |
| `apps/workflow_execution/tests/test_stage_engine.py` | Created — 20 tests |

---

## 7. Manual QA Checklist

- [ ] Create a workflow with nodes: `start → action → approval → action → end`
- [ ] Start the workflow via `POST /api/v1/workflow/instances/start/`
- [ ] Confirm `GET /api/v1/workflow/instances/{id}/wait-states/` returns 1 record with `status=waiting`
- [ ] Confirm `GET /api/v1/workflow/instances/{id}/transition-logs/` shows the `start → action` and `action → approval` transitions
- [ ] Resume via `POST /api/v1/workflow/instances/{id}/resume/` — confirm advances to next stage
- [ ] Create a `WorkflowStageTransition` with `condition_config: {"field": "score", "op": "gte", "value": 80}` and a fallback transition with empty conditions at higher priority number
- [ ] Start instance with `context: {"score": 90}` — confirm high-score path taken
- [ ] Start instance with `context: {"score": 60}` — confirm fallback path taken
- [ ] Skip a waiting stage via `POST /api/v1/workflow/instances/{id}/skip/` — confirm `stage_execution.status = skipped` and wait state `cancelled`
- [ ] Fail an instance via `POST /api/v1/workflow/instances/{id}/fail/` — confirm `instance.status = failed`
- [ ] Check `GET /api/v1/workflow/instances/{id}/timeline/` shows actor and metadata on each entry

---

## 8. Condition Config Reference

```json
// Single condition
{
  "field": "score",
  "op": "gt",
  "value": 70
}

// AND group
{
  "operator": "and",
  "conditions": [
    {"field": "score", "op": "gte", "value": 70},
    {"field": "department", "op": "eq", "value": "engineering"}
  ]
}

// OR group
{
  "operator": "or",
  "conditions": [
    {"field": "source", "op": "eq", "value": "agency"},
    {"field": "score", "op": "gte", "value": 90}
  ]
}
```

**Supported `op` values:** `eq` `ne` `gt` `gte` `lt` `lte` `contains` `not_contains` `in` `not_in`

---

## 9. Known Constraints

- `WorkflowStageTransition` rows for a workflow entirely replace edge-based routing for that `from_stage_id`. If no transitions exist for a node, raw `WorkflowEdge` conditions are used as fallback.
- `in` / `not_in` operators expect the filter `value` to be a JSON list: `["agency", "partner"]`
- `skip_stage()` will cancel the open `WorkflowWaitState` if one exists, but does not cancel other open wait states for the same instance
- `resume_by_event()` matches on both `WorkflowWaitState.resume_event` (explicit) and `WorkflowInstance.wait_reason` → `WAIT_REASON_RESUME_EVENTS` mapping (implicit)
