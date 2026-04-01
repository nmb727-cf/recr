# UI Spec — Interview Command Center

**Module:** `apps/interviews`
**Last updated:** 2026-03-28
**Audience:** Frontend engineers implementing against the Interview API.

All requests require `Authorization: Bearer <access_token>`.
All responses follow the envelope: `{ success, data, message, meta? }`.

---

## Base URL

```
/api/v1/interviews/
```

---

## Screens & Endpoint Mapping

### 1. Interview Types Management

> Admin / HR Manager screen for managing the interview format catalog.

#### List types
```
GET /api/v1/interviews/types/
```
**Response:**
```json
{
  "success": true,
  "data": {
    "types": [
      {
        "id": "uuid",
        "name": "Technical",
        "code": "technical",
        "description": "...",
        "is_active": true,
        "created_at": "ISO8601",
        "updated_at": "ISO8601"
      }
    ]
  },
  "message": "Interview types retrieved.",
  "meta": { "total": 9 }
}
```
**UI notes:**
- Only show `is_active: true` types in dropdowns.
- Admin screens may show all, with toggle to activate/deactivate.

#### Create type
```
POST /api/v1/interviews/types/
Content-Type: application/json

{ "name": "Technical", "code": "technical", "description": "..." }
```
**Required fields:** `name`, `code`
**Errors:** `400` if `code` already exists.

#### Update / soft-delete type
```
PUT    /api/v1/interviews/types/<id>/
DELETE /api/v1/interviews/types/<id>/
```

---

### 2. Interview Templates

> Recruiter screen to define reusable interview configurations.

#### List templates (tenant-scoped)
```
GET /api/v1/interviews/templates/
```
**Response data key:** `templates` — array of template objects.
**Fields of interest:**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `name` | string | Display name |
| `interview_type` | string | Legacy code string (`ai_screening`, `panel`, …) |
| `type` | uuid\|null | FK to `InterviewType` catalog |
| `type_name` | string\|null | Resolved display name from catalog |
| `duration_minutes` | int | |
| `scoring_type` | `numeric`\|`pass_fail`\|`criteria` | Drives score input UI |
| `passing_threshold` | decimal | Show as percentage |
| `questions` | array | Array of `{ text, type, options?, duration? }` |
| `is_active` | bool | Only active templates shown in schedule form |

#### Create template
```
POST /api/v1/interviews/templates/
```
**Writable fields:** `name`, `interview_type`, `type` (uuid), `duration_minutes`, `instructions`, `scoring_type`, `passing_threshold`, `auto_shortlist_above`, `auto_reject_below`, `anti_cheat_enabled`, `recording_enabled`, `questions` (JSON array), `scoring_criteria` (JSON dict).

#### Update / delete template
```
PUT    /api/v1/interviews/templates/<id>/
DELETE /api/v1/interviews/templates/<id>/
```
DELETE is a soft delete — template disappears from lists but historical interviews are unaffected.

---

### 3. Schedule an Interview

> Triggered from pipeline board, candidate profile, or application drawer.

```
POST /api/v1/interviews/
Content-Type: application/json
```
**Payload:**
```json
{
  "application_id": "uuid",
  "candidate_id": "uuid",
  "requisition_id": "uuid",
  "interview_type": "panel",
  "interview_round": 2,
  "title": "Final Panel",
  "scheduled_at": "2026-04-10T10:00:00Z",
  "template_id": "uuid",
  "interview_link": "https://meet.example.com/abc",
  "panelist_ids": ["uuid-user-1", "uuid-user-2"]
}
```
**Required:** `application_id`, `candidate_id`, `requisition_id`, `interview_type`.
**Optional:** `template_id` (auto-seeds questions), `panelist_ids` (assigns panelists).

**Success response:** `201`, `data.interview` — full interview object.

**UI notes:**
- Populate `interview_type` from `GET /interviews/types/`.
- Populate `template_id` from `GET /interviews/templates/`.
- `panelist_ids` — user picker limited to tenant users with `interviewer` role.

---

### 4. Interview List View

> Table/board view showing all interviews for the tenant.

```
GET /api/v1/interviews/
```
**Query params:**

| Param | Type | Effect |
|---|---|---|
| `status` | string | Filter by status |
| `candidate_id` | uuid | Filter by candidate |
| `application_id` | uuid | Filter by application |
| `type` | string | Filter by `interview_type` code |

**Response data key:** `interviews` — array.
**Response meta:** `{ total: N }` — use for pagination display.

**Status values and badge colours:**

| Status | Suggested colour |
|---|---|
| `scheduled` | Blue |
| `in_progress` | Amber |
| `completed` | Green |
| `cancelled` | Red |
| `no_show` | Grey |
| `rescheduled` | Purple |

---

### 5. Interview Detail View

```
GET /api/v1/interviews/<id>/
```
**Response data keys:** `interview`, `panelists`, `questions`.
The `interview` object includes an inline `decision` field (null if not yet recorded).

**Embedded `decision` shape:**
```json
{
  "id": "uuid",
  "decision": "hire",
  "notes": "Strong candidate.",
  "decided_by": "uuid",
  "decided_at": "ISO8601"
}
```

---

### 6. Interview Lifecycle Actions

All are `POST` — no request body required unless noted.

#### Start
```
POST /api/v1/interviews/<id>/start/
```
Transitions `scheduled → in_progress`. Enable once `scheduled_at` is reached.
**Error if not `scheduled`:** `400 { "message": "Cannot start interview in status '...'." }`

#### Complete
```
POST /api/v1/interviews/<id>/complete/
Body (optional):
{
  "overall_score": 82.5,
  "recommendation": "recommend",
  "feedback_summary": "Solid communication skills."
}
```
Transitions `in_progress → completed`.

**`recommendation` choices:**
`strongly_recommend` | `recommend` | `neutral` | `not_recommend` | `reject`

#### Cancel
```
POST /api/v1/interviews/<id>/cancel/
Body (optional): { "reason": "Candidate withdrew" }
```

#### Reschedule
```
POST /api/v1/interviews/<id>/reschedule/
Body: { "scheduled_at": "ISO8601" }
```

---

### 7. Structured Feedback (Panelist)

> Each panelist submits feedback post-interview. One record per panelist — submit is idempotent.

#### View all feedback for an interview
```
GET /api/v1/interviews/<id>/structured-feedback/
```
**Response data key:** `feedback` — array of feedback objects.

**Feedback object:**
```json
{
  "id": "uuid",
  "panelist_id": "uuid",
  "score": 75.0,
  "notes": "Good problem-solving.",
  "recommendation": "hire",
  "criteria_scores": {
    "communication": 80,
    "technical_depth": 70,
    "culture_fit": 75
  },
  "submitted_at": "ISO8601"
}
```

#### Submit / update feedback
```
POST /api/v1/interviews/<id>/structured-feedback/
Content-Type: application/json
```
**Payload:**
```json
{
  "score": 75.0,
  "notes": "Good problem-solving.",
  "recommendation": "hire",
  "criteria_scores": { "communication": 80, "technical_depth": 70 }
}
```
**`recommendation` choices:** `hire` | `reject` | `hold` | `next_round`

**UI notes:**
- Score input type depends on `template.scoring_type`:
  - `numeric` → number input (0–100)
  - `pass_fail` → toggle (Pass / Fail → map to score 100 / 0)
  - `criteria` → per-criterion sliders, populate keys from `template.scoring_criteria`
- Submitting updates `interview.human_score` (server-calculated average).
- Lock form once interview status is `cancelled`.

---

### 8. Final Decision

> HR Manager / Hiring Manager records the final call after all feedback is in.

#### Get decision
```
GET /api/v1/interviews/<id>/decision/
```
Returns `404` if not yet recorded.

#### Record / update decision
```
POST /api/v1/interviews/<id>/decision/
Content-Type: application/json

{ "decision": "hire", "notes": "Unanimous panel recommendation." }
```
**`decision` choices:** `hire` | `reject` | `hold` | `next_round`

**UI notes:**
- Only show decision form when `interview.status === 'completed'`.
- Form is editable (POST is upsert) — allow correction before it propagates downstream.
- After `hire` decision, surface "Create Offer" CTA.
- After `next_round` decision, surface "Schedule Next Round" CTA (pre-fill `interview_round + 1`).

---

## Candidate-Facing Endpoints

Mounted at `/api/v1/candidate/interviews/` (separate URL prefix).

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Candidate's own interview list |
| `/<id>/start/` | POST | Candidate starts their async interview |
| `/<id>/submit-answer/` | POST | Submit answer for one question |
| `/<id>/complete/` | POST | Mark interview done |

**Submit answer payload:**
```json
{
  "question_id": "uuid",
  "answer_text": "...",
  "video_url": "https://..."
}
```

---

## Error Reference

| HTTP | Meaning | When |
|---|---|---|
| `400` | Validation error | Missing/invalid fields; invalid status transition |
| `401` | Unauthenticated | No or expired JWT |
| `403` | Forbidden | Authenticated but missing RBAC permission |
| `404` | Not found | Wrong ID or wrong tenant |

Error envelope:
```json
{
  "success": false,
  "data": null,
  "message": "Human-readable error.",
  "errors": { "field": ["error detail"] }
}
```
