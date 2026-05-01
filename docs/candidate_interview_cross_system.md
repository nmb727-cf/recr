# Candidate Interview Cross-System Audit
**Date:** 2026-04-02  
**Scope:** Candidate-side interview experience vs. Interview Command Center (ICC) architecture  
**Method:** Direct code audit — backend models, views, automation signals, candidate URL routes, frontend pages

---

## 1. Supported Interview Types

### Backend Registry
The ICC defines **36+ interview type codes** (`INTERVIEW_TYPE_REGISTRY_DEFAULTS` in `apps/interviews/models.py`), grouped by `execution_mode`:

| Execution Mode | Types |
|---|---|
| `native` | ai_screening, ai_technical, ai_behavioral, one_way_video, coding_interview, mcq_assessment, aptitude, language, live_video, interview_cafe |
| `async` | async_text, async_audio, take_home_assignment |
| `manual` | recruiter_screening, phone_interview, technical_interview, system_design, debugging_interview, whiteboard, behavioral, culture_fit, hr_interview, leadership, executive, hiring_manager, panel, sequential, stakeholder, bar_raiser, final_round, case_study, role_play, presentation, portfolio_review, group_discussion, mock, campus, walkin |
| `third_party` | psychometric, cognitive, assessment_center |
| `external` | work_sample |

### Candidate UI Mapping
`CandidateInterviewRuntime.tsx` maps types to 9 render modes via `getExecutionMode()`:

| Runtime Mode | Types Matched | UI Rendered |
|---|---|---|
| `ai` | `*ai*`, `one_way_video`, `async_text_interview` | Text area for response |
| `assessment` | `*assessment*`, `aptitude_test`, `case_study`, `work_sample_test` | Radio group (MCQ) or text area |
| `video` | `*video*`, `one_way_video`, `prerecorded_video`, `live_video` | Recording shell placeholder + notes |
| `human` | `*panel*`, `*hr*`, `*leadership*`, `*executive*` | Waiting screen with meeting link prompt |
| `group` | `group_discussion` | Waiting room shell |
| `presentation` | `presentation_interview` | Notes area |
| `role_play` | `role_play` | Text response |
| `portfolio` | `portfolio_review` | Text response |
| `technical` | `*technical*`, `coding_interview`, `system_design`, `debugging_interview`, `whiteboard_interview` | Text area |
| `generic` | everything else | Text area |

### Coverage Gaps — Interview Types

| Type | Gap |
|---|---|
| `one_way_video` | Mapped to BOTH `ai` (line 71) AND `video` (line 73) — `ai` wins due to short-circuit, so video shell never renders for this type |
| `take_home_assignment` | Falls to `generic` — no assignment upload URL field is actually sent to backend (file picker stores filename locally only, `assignmentUrl` just stores the filename string) |
| `async_text` | Mapped as `ai` (text area) — correct, but `async_text_interview` string match fails if backend sends `async_text` (exact string mismatch) |
| `phone_interview` | Renders `generic` text area — acceptable, but no phone number / dial-in info display |
| `recruiter_screening` | Falls to `generic` — no scheduling/calendar context shown |
| `coding_interview` | Text area only — no code editor, no syntax highlighting |
| `system_design` | Text area only — no whiteboard or diagram tool |
| `debugging_interview` | Text area only — no code execution environment |
| Video recording (all types) | Recording UI is a **placeholder shell only** — no actual video capture, no WebRTC, no media stream |
| `prerecorded_video` | Not in `INTERVIEW_TYPE_CODES` backend list — will never be set by company side |
| `async_audio` | Falls to `generic` — no audio recording UI |

---

## 2. Scheduling Support

### What Works
| Feature | Status |
|---|---|
| View scheduled interview (date, time) | **Working** — `scheduled_at` shown via `dayjs().format()` in `CandidateInterviewDashboard` |
| View interview type, title, instructions | **Working** |
| Secure runtime URL (token-based) | **Working** — auto-generated, 30-min pre-window, 8-hr post-window |
| Self-reschedule | **Partial** — button visible only if `scheduling_link_token` / `scheduling_token` is set on interview; navigates to `/interviews/scheduling/self/:token` (CandidateSelfSchedule page exists) |
| Accept/Confirm interview | **Missing** — no candidate accept/confirm action |
| Candidate-initiated cancel | **Missing** — no cancel endpoint in `candidate_urls.py`, no UI |
| Timezone display | **Partial** — shown in raw UTC/server time via `dayjs()`, no user timezone conversion |
| Interviewer name/details | **Missing** — `InterviewSerializer` does not expose interviewer profile names to candidate; only `candidate_id` is used to filter |
| Calendar invite / ICS file | **Missing** — no `.ics` download or calendar add link for candidate |

### Self-Schedule Flow
`getReschedulePath()` in `CandidateInterviewDashboard` checks for `scheduling_link_token` on the interview row. This token is only present if the company side explicitly enabled candidate self-scheduling via the Scheduling Engine. If not enabled, reschedule button is disabled. Correct behavior — but the button label says "Reschedule" which is misleading if first-time scheduling was intended.

---

## 3. Pre-Qualification Engine

### Company Side
ICC has a full Pre-Qualification Engine:
- Form Builder with sections and questions
- Routing rules
- Knockout logic (`auto_reject_enabled` flag)
- Eligibility forms
- Prequalification forms attached to requisitions

### Candidate Side
**This feature is entirely missing on the candidate side.**

| Check | Status |
|---|---|
| Candidate receives prequalification form | **Missing** — no candidate route, no frontend page |
| Candidate can submit form | **Missing** — all `/api/v1/prequalification/` endpoints are behind `CanViewPrequalForms` permission (company role only) |
| Candidate sees knockout rejection | **Missing** — automation event `prequalification.completed` exists but no candidate-facing result page |
| Candidate sees pass → next stage | **Missing** |

**Impact:** Any requisition configured with a pre-qualification gate has no candidate-facing delivery path. The form exists only in the company admin UI.

---

## 4. Live Interview Engine

| Feature | Status |
|---|---|
| Join live interview via `meeting_link` | **Working** — "Join Meeting" button rendered when `interview.meeting_link` is set |
| External interview link | **Working** — "Open External Interview" button rendered when `external_interview_link` is set |
| View interview instructions | **Working** — fetched from `InterviewTemplate.instructions` via `CandidateInterviewInstructionsView` |
| Start state | **Working** — `candidateStart()` API sets `in_progress`, activates session |
| End state | **Working** — `candidateComplete()` API sets `completed_at`, navigates to status page |
| Expired access | **Working** — token expiry redirects to `/candidate/interviews/expired` |
| Blocked/locked session | **Working** — `session_locked`, `token_invalid`, `attempt_blocked` redirect to `/candidate/interviews/blocked` |
| Actual video capture / WebRTC | **Missing** — video shell is a static placeholder only |
| Screenshare / recording consent | **Missing** |
| Join link for `live_video` type | **Partial** — only works if company side sets `meeting_link` on the interview; ICC does not auto-generate a video room |

---

## 5. Scorecard / Evaluation Impact

### Backend
Scorecard system exists in ICC (`InterviewScorecard`, `InterviewPanelist`, `InterviewFeedbackSubmission`). `CandidateInterviewStatusView` exists.

### Candidate Side

| Feature | Status |
|---|---|
| View interview status (completed/pending/missed) | **Working** — `CandidateInterviewStatus.tsx` and `CandidateInterviewResults.tsx` exist |
| View pass/fail outcome | **Missing** — `CandidateInterviewResults.tsx` shows: *"Recruiter feedback and improvement suggestions appear when visible."* — static placeholder text, no real data rendered |
| View feedback (when `feedback_visible=true`) | **Missing** — no API call to fetch scorecard or feedback for candidate |
| Next stage movement notification | **Partial** — dependent on automation rules triggering a notification; no direct stage outcome shown on interview result page |
| Score or rating visible to candidate | **Missing** (intentional — scorecards are recruiter-internal; but even `feedback_visible` toggle has no effect candidate-side) |

---

## 6. Automation Impact

### Automation Events Wired (backend)

| Event | Signal Connected | Email Template |
|---|---|---|
| `interview.scheduled` | ✓ `on_interview_scheduled` | `interview_invite` (has date/time/mode vars) |
| `interview.completed` | ✓ `on_interview_completed` | Configured via automation rules |
| `interview.cancelled` | ✓ `on_interview_cancelled` | Configured via automation rules |
| `candidate.no_show` | ✓ (via cancelled signal) | Configured via automation rules |
| `prequalification.completed` | Listed in trigger events | No signal connected |
| Interview reminder (24h/1h) | **Not in trigger events** | **Missing** |
| Next stage notification | `application.stage_changed` | Configured via automation rules |
| Rejection notification | `application.stage_changed` | `rejection_after_interview` template exists |

### Candidate Notification Display
Unread notifications appear in `CandidateCommandCenter` via `notificationsApi.list({ is_read: false })`. Notification bell exists. Mark-read works.

**Gap:** There is no interview reminder automation trigger event (`interview.reminder_24h`, `interview.reminder_1h`). Candidates must rely on the original invite email to remember their interview time.

---

## 7. Cross-System Sync

| Scenario | Status |
|---|---|
| Company schedules interview → Candidate sees it | **Working** — same `Interview` model, `CandidateInterviewListView` filters by `candidate_id` |
| Company reschedules → Candidate sees updated time | **Working** — `interview.status = 'rescheduled'`, `scheduled_at` updated; candidate list re-fetches |
| Company cancels → Candidate sees cancel | **Partial** — `interview.status = 'cancelled'`; candidate dashboard does NOT explicitly filter out or flag cancelled interviews — they will still appear in the list without a "Cancelled" bucket |
| Candidate submits answer → Company sees submission | **Working** — `CandidateSubmitAnswerView` creates `InterviewAnswer`; ICC can query answers |
| Candidate completes interview → Company sees | **Working** — `CandidateCompleteInterviewView` sets `completed_at`; ICC shows completed status |
| Candidate no-shows → Automation fires | **Working** — backend sets `status = 'no_show'`, `candidate_status = 'missed'` in list response |
| Company scorecard score → Candidate feedback page | **Broken** — no data pipeline from scorecard to candidate result page |

---

## 8. Missing Features

| # | Feature | Impact |
|---|---|---|
| M1 | Pre-qualification form delivery to candidate | High — blocking for PQ-gated requisitions |
| M2 | Candidate-initiated interview cancel | Medium — candidates must contact recruiter directly |
| M3 | Interview reminder automation event | Medium — candidates have no reminder system |
| M4 | Scorecard feedback visible to candidate | Medium — `CandidateInterviewResults` is a shell |
| M5 | Actual video capture (one_way_video, async_audio) | High — core native types have no recording mechanism |
| M6 | Timezone localisation for scheduled_at | Medium — all times shown in server timezone |
| M7 | Interviewer name/details on candidate view | Low — candidates don't know who's interviewing them |
| M8 | Calendar ICS / "Add to Calendar" for candidates | Low — UX gap |
| M9 | Accept/Confirm interview action | Low — no confirmation mechanism |
| M10 | Code editor for coding_interview type | Medium — text area degrades the coding interview experience |

---

## 9. Broken Features

| # | Feature | Location | Detail |
|---|---|---|---|
| B1 | `one_way_video` maps to wrong mode | `CandidateInterviewRuntime.tsx:71–73` | `ai` wins before `video` — video shell never renders for this type |
| B2 | `async_text` string mismatch | `CandidateInterviewRuntime.tsx:71` | Backend code is `async_text`; frontend checks for `async_text_interview` — no match, falls to `generic` |
| B3 | Cancelled interviews not bucketed | `CandidateInterviewListView` + Dashboard | No `cancelled` bucket; cancelled interviews appear mixed in the list without visual distinction |
| B4 | `take_home_assignment` upload is filename-only | `CandidateInterviewRuntime.tsx:350–354` | `assignmentUrl` stores only the local filename string; no actual file upload to backend |
| B5 | Prequalification endpoints require company permission | `apps/prequalification/views.py` | `CanViewPrequalForms` permission blocks candidates from accessing forms |
| B6 | `CandidateInterviewResults` is a static shell | `CandidateInterviewResults.tsx:261` | Shows placeholder text, no real scorecard or feedback data |

---

## 10. Fix Priority

| Priority | Item | Effort |
|---|---|---|
| **P1 — High** | M1: Pre-qualification candidate form delivery | New candidate route + backend permission + form renderer |
| **P1 — High** | B3: Cancelled interviews not shown distinctly to candidate | Add `cancelled` bucket in `CandidateInterviewListView`; filter in dashboard |
| **P1 — High** | B1: `one_way_video` mode detection bug | Swap check order in `getExecutionMode()` — video before ai |
| **P1 — High** | B2: `async_text` string mismatch | Change frontend check to `async_text` (match backend code) |
| **P2 — Medium** | M5: Video capture for native types | Requires MediaRecorder/WebRTC integration — significant build |
| **P2 — Medium** | M4: Scorecard feedback visible to candidate | Add `feedback_visible` field to InterviewSerializer; build feedback card in Results page |
| **P2 — Medium** | M3: Interview reminder automation | Add `interview.reminder_24h` trigger event; connect Celery beat job |
| **P2 — Medium** | B4: Take-home assignment upload | Replace local filename with actual file upload to `/documents/` |
| **P3 — Low** | M6: Timezone localisation | Use `dayjs-timezone` with user's stored tz preference |
| **P3 — Low** | M2: Candidate cancel | Add `DELETE /candidate/interviews/:id/` or cancel endpoint + UI |
| **P3 — Low** | M10: Code editor | Integrate CodeMirror or Monaco for `coding_interview` type |
| **P3 — Low** | M7: Interviewer details | Add interviewer name to InterviewSerializer (candidate-safe fields only) |
| **P3 — Low** | M8: Add to calendar | Generate ICS from `scheduled_at` + `duration_minutes` |
