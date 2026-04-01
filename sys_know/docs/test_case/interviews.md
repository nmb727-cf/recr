# Test Cases — Interview Command Center

**Module:** `apps/interviews`
**Last updated:** 2026-03-28

---

## Models

### InterviewType

| # | Test | Assertion |
|---|---|---|
| M-T-01 | Create with valid name + code | Saved, `is_active=True`, `is_deleted=False` |
| M-T-02 | Duplicate `code` | `IntegrityError` (unique constraint) |
| M-T-03 | `soft_delete()` | `is_deleted=True`, `deleted_at` populated |
| M-T-04 | Filter active types | `is_deleted=False` + `is_active=True` only |

### InterviewTemplate

| # | Test | Assertion |
|---|---|---|
| M-TM-01 | Create with `tenant_id`, `name`, `interview_type` | Saved with `scoring_type='numeric'` default |
| M-TM-02 | `type` FK null (legacy template) | Allowed — nullable FK |
| M-TM-03 | `type` FK points to deleted `InterviewType` | FK set to NULL (`SET_NULL`) |
| M-TM-04 | `soft_delete()` | `is_deleted=True`, `deleted_at` set |
| M-TM-05 | Template from different tenant not visible | Filter by `tenant_id` excludes it |

### Interview

| # | Test | Assertion |
|---|---|---|
| M-I-01 | Create with required fields | `status='scheduled'`, `is_deleted=False` |
| M-I-02 | `soft_delete()` | `is_deleted=True`, `deleted_at` set |
| M-I-03 | Default ordering | Queryset ordered by `-created_at` |
| M-I-04 | Cross-tenant query isolation | `tenant_id` filter excludes other tenants |

### InterviewFeedback

| # | Test | Assertion |
|---|---|---|
| M-F-01 | Two feedbacks for same `(interview_id, panelist_id)` | `IntegrityError` (unique_together) |
| M-F-02 | `soft_delete()` | `is_deleted=True`, `deleted_at` set |
| M-F-03 | `score=None` allowed | Saved without error |
| M-F-04 | `criteria_scores` stores dict | JSONField persists arbitrary structure |

### InterviewDecision

| # | Test | Assertion |
|---|---|---|
| M-D-01 | Two decisions for same `interview_id` | `IntegrityError` (unique on `interview_id`) |
| M-D-02 | Valid `decision` choices | `hire`, `reject`, `hold`, `next_round` accepted |
| M-D-03 | Invalid `decision` value | Rejected at serializer validation |

---

## Services

### InterviewService

| # | Test | Input | Expected |
|---|---|---|---|
| S-I-01 | `create()` schedules interview | valid kwargs | Interview saved, `status='scheduled'` |
| S-I-02 | `create()` with valid `template_id` | template with 2 questions | 2 `InterviewQuestion` rows created |
| S-I-03 | `create()` with invalid `template_id` | non-existent UUID | Interview created, no questions (silent) |
| S-I-04 | `create()` fires event | — | `events.interview.scheduled` received |
| S-I-05 | `start()` from `scheduled` | interview.status='scheduled' | `status='in_progress'`, `started_at` set |
| S-I-06 | `start()` from `completed` | interview.status='completed' | `ValueError` raised |
| S-I-07 | `complete()` from `in_progress` | score, recommendation | `status='completed'`, `completed_at` set |
| S-I-08 | `complete()` aggregates feedback scores | 3 feedback rows with scores 60,70,80 | `human_score=70.0` |
| S-I-09 | `complete()` fires events | — | `events.interview.completed` + `events.application.interviewed` |
| S-I-10 | `complete()` application missing | no matching Application | Completes silently, no crash |
| S-I-11 | `cancel()` from `scheduled` | reason='no show' | `status='cancelled'`, reason in `feedback_summary` |
| S-I-12 | `cancel()` from `completed` | — | `ValueError` raised |
| S-I-13 | `reschedule()` | new datetime | `scheduled_at` updated, `status='rescheduled'` |
| S-I-14 | `add_panelist()` idempotent | same user twice | Second call returns existing row, no duplicate |

### InterviewFeedbackService

| # | Test | Input | Expected |
|---|---|---|---|
| S-F-01 | `submit()` creates new record | valid kwargs | `InterviewFeedback` row created |
| S-F-02 | `submit()` updates existing record | same `(interview_id, panelist_id)` | Row updated, not duplicated |
| S-F-03 | `submit()` recalculates `human_score` | 2 existing scores 50,90 + new 70 | `Interview.human_score=70.0` |
| S-F-04 | `submit()` with `score=None` | score omitted | Avg recalc ignores null scores |

### InterviewDecisionService

| # | Test | Input | Expected |
|---|---|---|---|
| S-D-01 | `record()` creates new decision | valid kwargs | `InterviewDecision` row created |
| S-D-02 | `record()` updates existing decision | same `interview_id` | Row updated (`update_or_create`) |
| S-D-03 | `record()` fires event | — | `events.interview.decision_recorded` with `created=True/False` |
| S-D-04 | `get_for_interview()` no decision | no row | Returns `None` |

---

## API Endpoints

### Auth & Tenant Isolation

| # | Test | Expected |
|---|---|---|
| A-01 | All endpoints without JWT | `401 Unauthorized` |
| A-02 | GET `/interviews/` with valid JWT | Returns only caller's tenant interviews |
| A-03 | GET `/interviews/<id>/` with valid JWT but wrong tenant | `404 Not Found` |
| A-04 | POST `/interviews/<id>/decision/` with correct tenant | `200 OK` |

### RBAC

| # | Endpoint | Missing Permission | Expected |
|---|---|---|---|
| R-01 | `GET /interviews/types/` | `interviews.type.view` | `403 Forbidden` |
| R-02 | `POST /interviews/types/` | `interviews.type.manage` | `403 Forbidden` |
| R-03 | `POST /interviews/` | `interviews.interview.create` | `403 Forbidden` |
| R-04 | `POST /interviews/<id>/start/` | `interviews.interview.start` | `403 Forbidden` |
| R-05 | `POST /interviews/<id>/decision/` | `interviews.decision.record` | `403 Forbidden` |
| R-06 | `POST /interviews/<id>/structured-feedback/` | `interviews.feedback.submit` | `403 Forbidden` |

### GET /interviews/types/

| # | Scenario | Expected |
|---|---|---|
| E-TY-01 | Valid request | `200`, list of active types |
| E-TY-02 | Deleted type exists | Not included in response |

### POST /interviews/types/

| # | Scenario | Expected |
|---|---|---|
| E-TY-03 | Valid `name` + unique `code` | `201`, type object returned |
| E-TY-04 | Duplicate `code` | `400` validation error |
| E-TY-05 | Missing `name` | `400` validation error |

### GET/POST /interviews/templates/

| # | Scenario | Expected |
|---|---|---|
| E-TM-01 | GET — own templates only | `200`, filtered by `tenant_id` |
| E-TM-02 | POST valid payload | `201`, template object returned |
| E-TM-03 | POST missing `name` | `400` |
| E-TM-04 | DELETE — soft deletes | Template excluded from future GET |

### GET /interviews/

| # | Scenario | Expected |
|---|---|---|
| E-IL-01 | No filters | All tenant interviews returned |
| E-IL-02 | `?status=scheduled` | Only scheduled interviews |
| E-IL-03 | `?candidate_id=<uuid>` | Filtered by candidate |
| E-IL-04 | `?application_id=<uuid>` | Filtered by application |
| E-IL-05 | Response includes `meta.total` | Count matches list length |

### POST /interviews/

| # | Scenario | Expected |
|---|---|---|
| E-IC-01 | Valid payload, no template | `201`, `status='scheduled'`, no questions |
| E-IC-02 | Valid payload with `template_id` | `201`, questions seeded from template |
| E-IC-03 | `panelist_ids` provided | Panelist rows created |
| E-IC-04 | Missing required field | `400` validation error |

### POST /interviews/\<id\>/start/

| # | Scenario | Expected |
|---|---|---|
| E-IS-01 | Interview in `scheduled` state | `200`, `status='in_progress'`, `started_at` set |
| E-IS-02 | Interview already `in_progress` | `400` error message |
| E-IS-03 | Interview `completed` | `400` error message |
| E-IS-04 | Wrong tenant interview | `404` |

### POST /interviews/\<id\>/complete/

| # | Scenario | Expected |
|---|---|---|
| E-IC-01 | Interview `in_progress` | `200`, `status='completed'` |
| E-IC-02 | Interview `scheduled` (not started) | `400` |
| E-IC-03 | With `overall_score` and `recommendation` | Fields persisted |

### POST /interviews/\<id\>/cancel/

| # | Scenario | Expected |
|---|---|---|
| E-CA-01 | Interview `scheduled` | `200`, `status='cancelled'` |
| E-CA-02 | Interview `completed` | `400` |
| E-CA-03 | `reason` provided | Appears in `feedback_summary` |

### GET+POST /interviews/\<id\>/structured-feedback/

| # | Scenario | Expected |
|---|---|---|
| E-SF-01 | GET — no feedback yet | `200`, empty list |
| E-SF-02 | POST valid `score` + `recommendation` | `200`, feedback record upserted |
| E-SF-03 | POST twice (same panelist) | Second call updates, not duplicates |
| E-SF-04 | POST invalid `recommendation` | `400` |
| E-SF-05 | POST updates `Interview.human_score` | Aggregate recalculated |

### GET+POST /interviews/\<id\>/decision/

| # | Scenario | Expected |
|---|---|---|
| E-DE-01 | GET — no decision recorded | `404` |
| E-DE-02 | POST valid `decision='hire'` | `200`, decision persisted |
| E-DE-03 | POST then POST again | Second updates, not duplicates |
| E-DE-04 | POST invalid `decision='maybe'` | `400` |
| E-DE-05 | GET after POST | Returns recorded decision |

---

## Events

| # | Action | Signal fired | kwargs |
|---|---|---|---|
| EV-01 | `InterviewService.create()` | `events.interview.scheduled` | `interview` |
| EV-02 | `InterviewService.start()` | `events.interview.started` | `interview` |
| EV-03 | `InterviewService.complete()` | `events.interview.completed` | `interview` |
| EV-03b | `InterviewService.complete()` (app found) | `events.application.interviewed` | `application`, `interview` |
| EV-04 | `InterviewService.cancel()` | `events.interview.cancelled` | `interview` |
| EV-05 | `InterviewDecisionService.record()` | `events.interview.decision_recorded` | `interview`, `decision`, `created` |
