# WF Phase 004: Cross-Entity Routing Engine

**Prompt ID:** `TOS-WF-CROSS-ENTITY-ROUTING-004`  
**Date:** `2026-04-08`  
**Status:** ✅ Complete

---

## Summary

Implements a cross-entity routing layer that lets workflows move across company, agency, candidate, recruiter, hiring manager, HR, and HRMS boundaries without losing process continuity or audit trail.

---

## Implementation Status

| Component | Status | File |
|-----------|--------|------|
| `WorkflowEntityRoute` model | ✅ Implemented | `models/routing.py` |
| `WorkflowActorAssignment` model | ✅ Implemented | `models/routing.py` |
| `WorkflowHandoffCheckpoint` model | ✅ Implemented | `models/routing.py` |
| `WorkflowRoutingRule` model | ✅ Implemented | `models/routing.py` |
| `WorkflowRouteTimelineLog` model | ✅ Implemented | `models/routing.py` |
| Migration `0004_cross_entity_routing` | ✅ Implemented | `migrations/0004_cross_entity_routing.py` |
| `ALLOWED_ROUTE_PAIRS` tenant-safety set | ✅ Implemented | `services/workflow_cross_entity_routing_engine.py` |
| `determine_next_route()` | ✅ Implemented | routing engine |
| `create_entity_route()` | ✅ Implemented | routing engine |
| `assign_actor_for_stage()` | ✅ Implemented | routing engine |
| `handoff_stage_control()` | ✅ Implemented | routing engine |
| `validate_cross_entity_route()` | ✅ Implemented | routing engine |
| `complete_handoff()` | ✅ Implemented | routing engine |
| `fail_handoff()` | ✅ Implemented | routing engine |
| `continue_after_handoff()` | ✅ Implemented | routing engine |
| `route_to_onboarding()` shortcut | ✅ Implemented | routing engine |
| `route_to_hrms()` shortcut | ✅ Implemented | routing engine |
| `apply_routing_rules()` stage hook | ✅ Implemented | routing engine |
| `complete_handoff_by_event()` | ✅ Implemented | routing engine |
| Serializers (5 models + 3 action) | ✅ Implemented | `api/serializers.py` |
| `WorkflowEntityRouteViewSet` | ✅ Implemented | `api/views.py` |
| `WorkflowActorAssignmentViewSet` | ✅ Implemented | `api/views.py` |
| `WorkflowHandoffCheckpointViewSet` | ✅ Implemented | `api/views.py` |
| `WorkflowRoutingRuleViewSet` | ✅ Implemented | `api/views.py` |
| `WorkflowRouteTimelineLogViewSet` | ✅ Implemented | `api/views.py` |
| Instance sub-actions (`/routes/`, `/assignments/`, `/handoffs/`, `/route-timeline/`, `/assign-actor/`) | ✅ Implemented | `api/views.py` |
| URL registration (5 new routers) | ✅ Implemented | `urls.py` |
| Tests — `test_routing_engine.py` | ✅ Implemented | `tests/test_routing_engine.py` |

---

## Models

### `WorkflowEntityRoute` (`wf_exec_entity_routes`)
Records one cross-entity routing hop within a workflow instance.

| Field | Type | Notes |
|-------|------|-------|
| `workflow_instance` | FK | Cascade |
| `from_entity_type` | CharField | Choices: entity types |
| `to_entity_type` | CharField | Choices: entity types |
| `route_type` | CharField | `ownership_transfer`, `action_handoff`, `approval_handoff`, `scheduling_handoff`, `communication_handoff`, `onboarding_handoff`, `workflow_continuation` |
| `route_reason` | TextField | Human-readable reason |
| `status` | CharField | `pending`, `active`, `completed`, `failed`, `cancelled` |
| `stage_id` | UUID | Stage that triggered this route |
| `completed_at` | DateTimeField | Set by `.complete()` |

Methods: `.complete()`, `.fail(reason)`

### `WorkflowActorAssignment` (`wf_exec_actor_assignments`)
Tracks ownership of a specific stage (who is responsible/reviewer/approver).

| Field | Type | Notes |
|-------|------|-------|
| `workflow_instance` | FK | Cascade |
| `stage_id` | UUID | Indexed |
| `actor_type` | CharField | `recruiter`, `hiring_manager`, `hr`, `agency_manager`, `agency_recruiter`, `interviewer`, `candidate`, `system` |
| `actor_id` | UUID | Nullable — omit for role-only assignment |
| `assignment_type` | CharField | `responsible`, `reviewer`, `approver`, `scheduler`, `coordinator`, `observer` |
| `status` | CharField | `active`, `completed`, `revoked`, `expired` |

Methods: `.complete()`, `.revoke()`

### `WorkflowHandoffCheckpoint` (`wf_exec_handoff_checkpoints`)
Explicit handoff record waiting on an external response before the workflow continues.

| Field | Type | Notes |
|-------|------|-------|
| `workflow_instance` | FK | Cascade |
| `stage_execution` | FK | SET_NULL |
| `handoff_from` / `handoff_to` | CharField | e.g. `company_recruiter` / `agency_recruiter` |
| `handoff_type` | CharField | `agency_to_company`, `company_to_agency`, `company_to_candidate`, `candidate_to_company`, `company_to_hr`, `workflow_to_hrms`, `recruiter_to_manager`, `manager_to_hr` |
| `payload` | JSONField | Data sent to receiving entity |
| `expected_response_event` | CharField | Event key that resolves this checkpoint |
| `status` | CharField | `pending`, `delivered`, `acknowledged`, `completed`, `failed`, `expired` |
| `response_payload` | JSONField | Merged into instance context on complete |

Methods: `.acknowledge(response_payload)`, `.complete(response_payload)`, `.fail(reason)`

### `WorkflowRoutingRule` (`wf_exec_routing_rules`)
Defines dynamic routing logic per workflow (and optionally per stage).

| Field | Type | Notes |
|-------|------|-------|
| `workflow_id` | UUID | Indexed |
| `stage_id` | UUID | Nullable — `None` = applies to all stages |
| `condition_config` | JSONField | Same format as `WorkflowStageTransition.condition_config` |
| `route_to_entity_type` | CharField | Target entity |
| `route_to_actor_type` | CharField | Target actor role |
| `route_config` | JSONField | `{ "assignment_type", "handoff_type", "expected_response_event" }` |
| `priority` | IntegerField | Lower = higher priority |
| `is_active` | BooleanField | Rules evaluated only when `True` |

### `WorkflowRouteTimelineLog` (`wf_exec_route_timeline`)
Append-only audit log for every routing event.

| Field | Type |
|-------|------|
| `workflow_instance` | FK |
| `route` | FK (nullable) |
| `action` | CharField |
| `from_actor` / `to_actor` | CharField |
| `reason` | TextField |

---

## Routing Engine

File: `backend/apps/workflow_execution/services/workflow_cross_entity_routing_engine.py`

### Tenant-Safe Route Pairs (`ALLOWED_ROUTE_PAIRS`)
```
company ↔ agency          company ↔ candidate       company ↔ recruiter
company ↔ hiring_manager  company ↔ hr              company ↔ onboarding
company ↔ hrms            company ↔ interviewer     company ↔ panel
agency ↔ candidate        agency ↔ recruiter
recruiter ↔ hiring_manager
hiring_manager ↔ hr
hr ↔ onboarding
onboarding ↔ hrms
```
Same-entity-type routes are always allowed. All others are rejected with a `WorkflowRouteTimelineLog` entry.

### Engine Methods

| Method | Description |
|--------|-------------|
| `determine_next_route(instance, stage_id, context)` | Returns first matching `WorkflowRoutingRule` (stage-specific first, then global) |
| `create_entity_route(instance, from, to, ...)` | Validates + persists route hop; returns `(route, error)` |
| `assign_actor_for_stage(instance, stage_id, actor_type, ...)` | Creates `WorkflowActorAssignment`; revokes previous `responsible` for same stage |
| `handoff_stage_control(instance, stage_exec, from, to, handoff_type, ...)` | Creates `WorkflowHandoffCheckpoint` + companion route |
| `validate_cross_entity_route(instance, from, to)` | Returns `(is_valid, error_str)` |
| `complete_handoff(handoff_id, response_payload, ...)` | Marks checkpoint completed, completes route, resumes workflow |
| `fail_handoff(handoff_id, reason, ...)` | Marks checkpoint + route failed |
| `continue_after_handoff(instance, checkpoint, ...)` | Merges response_payload into context, resumes stage engine |
| `route_to_onboarding(instance, stage_id, hr_actor_id, ...)` | Shortcut: company→HR route + assignment + `company_to_hr` checkpoint |
| `route_to_hrms(instance, stage_id, hrms_payload, ...)` | Shortcut: onboarding→HRMS handoff with `hrms_handoff_ready` event |
| `apply_routing_rules(instance, stage_id, context)` | Post-stage hook: evaluates rules, assigns actors, creates handoffs |
| `complete_handoff_by_event(event_key, tenant_id, entity_id, payload)` | Bulk-completes all pending checkpoints matching an event key |

---

## API Endpoints

### New standalone endpoints

| Method | URL | ViewSet | Description |
|--------|-----|---------|-------------|
| GET | `/api/v1/workflow/entity-routes/` | `WorkflowEntityRouteViewSet` | List all routes |
| GET | `/api/v1/workflow/entity-routes/{id}/` | — | Route detail |
| POST | `/api/v1/workflow/entity-routes/{id}/complete/` | — | Complete a route |
| POST | `/api/v1/workflow/entity-routes/{id}/fail/` | — | Fail a route |
| GET | `/api/v1/workflow/actor-assignments/` | `WorkflowActorAssignmentViewSet` | List assignments |
| GET | `/api/v1/workflow/actor-assignments/{id}/` | — | Assignment detail |
| POST | `/api/v1/workflow/actor-assignments/{id}/revoke/` | — | Revoke assignment |
| GET | `/api/v1/workflow/handoff-checkpoints/` | `WorkflowHandoffCheckpointViewSet` | List checkpoints |
| GET | `/api/v1/workflow/handoff-checkpoints/{id}/` | — | Checkpoint detail |
| POST | `/api/v1/workflow/handoff-checkpoints/{id}/acknowledge/` | — | Acknowledge handoff |
| POST | `/api/v1/workflow/handoff-checkpoints/{id}/complete/` | — | Complete handoff + resume workflow |
| POST | `/api/v1/workflow/handoff-checkpoints/{id}/fail/` | — | Fail handoff |
| GET | `/api/v1/workflow/routing-rules/` | `WorkflowRoutingRuleViewSet` | List rules |
| POST | `/api/v1/workflow/routing-rules/` | — | Create rule |
| PUT/PATCH | `/api/v1/workflow/routing-rules/{id}/` | — | Update rule |
| DELETE | `/api/v1/workflow/routing-rules/{id}/` | — | Delete rule |
| GET | `/api/v1/workflow/route-timeline/` | `WorkflowRouteTimelineLogViewSet` | List audit logs |

### Instance sub-resource endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/workflow/instances/{id}/routes/` | Instance's entity routes |
| GET | `/api/v1/workflow/instances/{id}/assignments/` | Active actor assignments |
| GET | `/api/v1/workflow/instances/{id}/handoffs/` | Handoff checkpoints |
| GET | `/api/v1/workflow/instances/{id}/route-timeline/` | Route audit log |
| POST | `/api/v1/workflow/instances/{id}/assign-actor/` | Assign actor to stage |

---

## Tests

File: `backend/apps/workflow_execution/tests/test_routing_engine.py`

| Test Class | Scenarios Covered |
|-----------|-------------------|
| `TestAgencyToCompanyRecruiterRoute` (5 tests) | Route created, recruiter assigned, previous responsible revoked, timeline log written, routing rule matches context |
| `TestCompanyToAgencyInterviewHandoff` (4 tests) | Handoff checkpoint created, checkpoint completed on event response, bulk complete by event key, failed handoff marks route+checkpoint failed |
| `TestOfferAcceptedRoutesToOnboarding` (4 tests) | HR assignment created, company→HR route created, checkpoint with correct event, no assignment without stage_id |
| `TestInvalidRoutePairBlocked` (6 tests) | candidate→hrms blocked, agency→hr blocked, timeline log written for blocked route, same-entity always allowed, validation error message, no DB row on blocked route |
| `TestHrmsHandoffCompletesWorkflow` (5 tests) | onboarding→HRMS route created, checkpoint with `hrms_handoff_ready` event, response payload merged into context, bulk complete by event, route marked completed after handoff |

**Total: 24 test cases across 5 test classes**

---

## Known Limitations / Follow-ups

| Item | Priority | Notes |
|------|----------|-------|
| `apply_routing_rules()` uses dynamic import for `ENTITY_TYPE_CHOICES` | Medium | Fragile — replace with direct import or pre-computed set |
| No cross-tenant entity_id validation in `validate_cross_entity_route()` | Low | Tenant isolation enforced by `tenant_id` on all models; entity-level cross-tenant check is caller responsibility |
| `WorkflowHandoffCheckpoint.fail()` does not propagate reason to `route_reason` | Low | Cosmetic — route_reason set separately in `fail_handoff()` |
| UI routing dashboard not yet built | Low | Tracked separately |
