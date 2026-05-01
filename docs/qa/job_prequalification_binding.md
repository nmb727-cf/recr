# Job Prequalification Binding — QA Document
**Date:** 2026-04-05  
**Scope:** Phase 2 — Binding the existing prequalification module to Jobs.

---

## 1. Audit Result — Existing Prequalification Module

| Component | Status | Notes |
|-----------|--------|-------|
| `PrequalForm` model (templates) | **COMPLETE** | Full CRUD, multi-section, metadata |
| `PrequalSection` model | **COMPLETE** | Ordered sections with titles |
| `PrequalQuestion` model | **COMPLETE** | 9 question types, `score_weight`, `is_knockout` |
| `PrequalRule` model | **COMPLETE** | 9 condition types, 8 action types, `outcome_code` |
| `PrequalResponse` model | **COMPLETE** | Stores candidate answers per form |
| Scoring system | **PARTIAL** | `score_weight` on questions; no DB-level aggregation. Score calculated at evaluation time. |
| Knockout logic | **COMPLETE** | `is_knockout` flag + `action_type='reject'` rule triggers auto-fail |
| Pass threshold | **PARTIAL** | Stored in `form.metadata.prequalification_engine.knockout_logic.pass_threshold`. No enforced model field. |
| Automation trigger | **COMPLETE** | `prequalification.completed` fires on every response submission |
| **Job binding** | **MISSING → ADDED** | No FK to `JobRequisition` existed. Added 5 fields this session. |
| **Pipeline integration** | **DISCONNECTED → ADDED** | Evaluation service added; Application `application_form_data` updated with result. |
| Admin UI (form builder) | **COMPLETE** | `PrequalificationBuilder.tsx` — sections, questions, rules, preset library |
| Candidate UI (form renderer) | **COMPLETE** | `CandidatePrequalification.tsx` — dynamic form, multi-section |
| InterviewPrequalificationEngine | **COMPLETE** | 5-step advanced builder with knockout/routing config in metadata |

---

## 2. Fields Added to `JobRequisition`

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `prequal_enabled` | BooleanField | `False` | Turns prequalification gate on/off |
| `prequal_form_id` | UUIDField (nullable) | `null` | FK-equivalent to `PrequalForm.id` |
| `prequal_threshold_override` | IntegerField (nullable) | `null` | Override form's default pass threshold (0-100). Null = use form default. |
| `prequal_pass_action` | CharField | `'advance'` | What happens on pass: `advance` or `manual_review` |
| `prequal_fail_action` | CharField | `'reject'` | What happens on fail: `reject`, `hold`, or `manual_review` |

**Migration:** `apps/jobs/migrations/0014_jobrequisition_prequal_fields.py`

---

## 3. Backend Services

### `apps/jobs/prequal_service.py`

#### `evaluate_candidate_prequal(job_id, candidate_id, tenant_id) → dict`

1. Loads `JobRequisition` prequal config
2. Loads `PrequalForm` by `prequal_form_id`
3. Loads all `PrequalQuestion`s (with `score_weight`, `is_knockout`, `rules`)
4. Loads most-recent `PrequalResponse` per question for this candidate
5. Evaluates each question:
   - Knockout questions: if any `action_type='reject'` rule fires → `knockout_triggered=True`
   - Score: sum of `score_weight` for questions where no reject rule fired
6. Compares score vs threshold (`prequal_threshold_override` or `form.metadata.pass_threshold` or default 70)
7. Returns:
   ```json
   {
     "eligible": true,
     "result": "pass|fail|manual_review|not_configured",
     "score": 85,
     "total_weight": 100,
     "earned_weight": 85,
     "threshold": 70,
     "knockout_triggered": false,
     "knockout_question": null,
     "action": "advance",
     "details": [...]
   }
   ```

#### `get_job_prequal_snapshot(job_id, tenant_id) → dict`

Returns aggregate stats for the Job Command Center widget:
- `enabled`, `form_id`, `form_name`, `threshold`
- `pass_count`, `fail_count`, `pending_count`, `total_submitted`
- `pass_rate` (int, 0-100)

---

## 4. API Endpoints Added

| Method | URL | Purpose |
|--------|-----|---------|
| `GET` | `/api/v1/jobs/requisitions/{id}/prequal-snapshot/` | Command Center widget data |
| `POST` | `/api/v1/jobs/requisitions/{id}/prequal-evaluate/` | Evaluate candidate responses + update Application |

### Evaluate request body:
```json
{
  "candidate_id": "<uuid>",
  "application_id": "<uuid>"  // optional — if provided, Application is updated
}
```

### Evaluate response:
```json
{
  "result": {
    "eligible": true,
    "result": "pass",
    "score": 85,
    "threshold": 70,
    "action": "advance",
    "knockout_triggered": false,
    "details": [...]
  }
}
```

---

## 5. Pipeline Integration

When `application_id` is provided to the evaluate endpoint:

| Prequal Result | Action | Application Status |
|----------------|--------|--------------------|
| `pass` + `advance` | Mark `metadata.prequal_passed_at` | No status change (pipeline engine advances) |
| `pass` + `manual_review` | Mark `metadata.prequal_flagged_for_review` | No status change |
| `fail` + `reject` | Auto-reject | `status = 'rejected'`, `rejection_reason = 'Failed prequalification screening.'` |
| `fail` + `hold` | Hold | `status = 'on_hold'` |
| `fail` + `manual_review` | Flag for review | `metadata.prequal_flagged_for_review = True` |

`application_form_data` fields set on evaluation:
- `prequal_result` — `'pass'` | `'fail'`
- `prequal_score` — int 0-100
- `prequal_threshold` — threshold used
- `prequal_action` — action taken
- `prequal_knockout` — bool

These are used by the snapshot endpoint to count pass/fail/pending.

---

## 6. UI Added

### Job Setup Studio — Step 5: Prequalification

Location: `frontend/src/pages/jobs/JobSetupStudio.tsx`  
Step index: 4 (inserted between Workflow and Interviews)

**Prequalification Gate card:**
- Enable/Disable `Switch`
- Form selector `Select` (fetches active forms from `GET /prequalification/forms/`)
- Threshold override `InputNumber` (0-100%)

**Pass / Fail Routing card (shown when enabled):**
- On Pass: Radio — Advance to Next Stage / Flag for Manual Review
- On Fail: Radio — Auto-Reject / Hold / Flag for Manual Review

**State management:**
- `prequalEnabled` (bool)
- `prequalFormId` (string | null)
- `prequalThreshold` (number | null)
- `prequalPassAction` (string)
- `prequalFailAction` (string)

All state loaded from job in edit mode, saved via `onFinish` payload.

**Review step** shows prequal config in the Launch Summary section.

---

### Job Command Center — PrequalificationWidget

Location: `frontend/src/pages/jobs/JobCommandCenterView.tsx`  
Placement: 4-column grid alongside Interview Intelligence, Interview Automation, Offer Intelligence

**Shows:**
- Enabled/disabled state
- Active form name
- Pass / Fail / Pending counts (3-stat row)
- Pass rate percentage
- Configured threshold
- Fail action setting

Data source: `GET /jobs/requisitions/{id}/prequal-snapshot/`

---

## 7. Data Flow

```
Candidate applies → Application created (status='applied')
  ↓
Candidate receives prequal form link (job's prequal_form_id)
  ↓
Candidate submits responses → CandidatePrequalSubmitView
  ↓
Automation trigger: 'prequalification.completed' fires
  ↓
Recruiter or automation calls POST /jobs/requisitions/{id}/prequal-evaluate/
  body: { candidate_id, application_id }
  ↓
evaluate_candidate_prequal() runs:
  - Loads questions + responses
  - Evaluates knockout rules
  - Calculates score vs threshold
  ↓
Application.application_form_data updated with result
Application.status may change (reject/hold)
  ↓
Command Center widget shows updated pass/fail/pending counts
```

---

## 8. Use Cases

### UC-1: Create job with prequal gate
1. Job Setup Studio → Step 5 (Prequal)
2. Toggle "Enable Prequalification" ON
3. Select form → "Engineering Screening Form"
4. Set threshold override → 75%
5. On Pass → Advance to Next Stage
6. On Fail → Auto-Reject
7. Save → `prequal_enabled=true`, `prequal_form_id`, `prequal_threshold_override=75` stored on job

### UC-2: Evaluate candidate
1. Candidate submits prequal form via candidate portal
2. Recruiter clicks "Evaluate" (or automation triggers it)
3. `POST /jobs/requisitions/{id}/prequal-evaluate/` with `candidate_id` + `application_id`
4. Result: `{ result: 'pass', score: 82, threshold: 75, action: 'advance' }`
5. Application `application_form_data.prequal_result = 'pass'`

### UC-3: View prequal stats in Command Center
1. Open Job Command Center for a prequal-enabled job
2. PrequalificationWidget shows: Pass: 12, Fail: 4, Pending: 3, Pass Rate: 75%
3. Shows form name and threshold

---

## 9. Edge Cases

| Case | Behavior |
|------|----------|
| Job prequal disabled | Evaluate returns `not_configured`; widget shows "No Prequalification Gate" |
| `prequal_form_id` set but form deleted | `get_job_prequal_snapshot` returns `enabled=False`; evaluate returns `not_configured` |
| Candidate has no responses | Score = 0 (0 earned weight), knockout not triggered → likely fail |
| `prequal_threshold_override = null` | Uses `form.metadata.prequalification_engine.knockout_logic.pass_threshold` or defaults to 70 |
| Knockout question fails | Immediate fail regardless of total score |
| `application_id` not provided to evaluate | Result returned but Application not modified |
| Candidate re-submits form | Latest response per question is used (query ordered by `-created_at`) |
| `prequal_fail_action = 'hold'` | Application status = `'on_hold'`; not rejected |

---

## 10. Test Scenarios

### Backend

```python
# T1: Create job with prequal config
PUT /api/v1/jobs/requisitions/{id}/
body: { prequal_enabled: true, prequal_form_id: "<uuid>", prequal_threshold_override: 70 }
# → 200 OK, job has prequal_enabled=true

# T2: Evaluate — passing candidate
POST /api/v1/jobs/requisitions/{id}/prequal-evaluate/
body: { candidate_id: "<uuid>", application_id: "<uuid>" }
# → result='pass', score>=70

# T3: Evaluate — failing candidate (score below threshold)
# → result='fail', action=prequal_fail_action

# T4: Evaluate — knockout triggered
# Question is_knockout=True, answer triggers reject rule
# → result='fail', knockout_triggered=True

# T5: Evaluate — no prequal configured
# Job with prequal_enabled=False
# → result='not_configured', eligible=True

# T6: Snapshot — active job
GET /api/v1/jobs/requisitions/{id}/prequal-snapshot/
# → enabled=True, form_name, pass_count, fail_count, pass_rate

# T7: Snapshot — job with no prequal
# → { enabled: false }

# T8: Auto-reject on fail
POST /api/v1/jobs/requisitions/{id}/prequal-evaluate/
# prequal_fail_action='reject', score below threshold
# → Application.status = 'rejected'

# T9: Hold on fail
# prequal_fail_action='hold'
# → Application.status = 'on_hold'
```

### Frontend

| Test | Steps | Expected |
|------|-------|----------|
| Step 5 renders | Job Setup Studio → Step 5 | Prequal card with toggle |
| Enable prequal | Toggle ON | Form selector + threshold input appear |
| Disable prequal | Toggle OFF | "No prequalification gate" state shows |
| Select form | Dropdown from prequal forms | Form name stored |
| Threshold input | Enter 75 | Value stored as number |
| Pass/fail routing | Select radio options | Values stored |
| Save job | Click Publish & Launch | `prequal_*` fields in API payload |
| Review step | Step 9 (Review) | Prequal section shows enabled/form/threshold/actions |
| Command Center widget | Open CC for prequal-enabled job | Widget shows stats |
| CC widget disabled | Open CC for job without prequal | Empty/disabled state |

---

## 11. Known Limitations / Phase 3 Items

| Item | Status |
|------|--------|
| Automatic evaluation trigger | Not implemented — currently manual or automation-rule triggered. Phase 3: Celery task on `prequalification.completed` auto-calls evaluate. |
| Multi-attempt handling | Latest response used; no submission limit enforced. |
| Prequal link delivery to candidate | Not automated — recruiter must manually share the form URL. Phase 3: auto-send form link on application. |
| Pass advancement to next pipeline stage | `prequal_pass_action='advance'` marks metadata but doesn't automatically move the candidate through stages. Full pipeline integration is Phase 3. |
| Form versioning | If form is updated after job config saved, evaluation uses current form. No snapshot at time of binding. |
