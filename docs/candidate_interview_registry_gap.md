# Candidate Interview Registry Gap Analysis
**Date:** 2026-04-02  
**Source:** `apps/interviews/models.py` (INTERVIEW_TYPE_REGISTRY_DEFAULTS) vs `CandidateInterviewRuntime.tsx` (getExecutionMode)  
**Finding:** One runtime page handles all 44 types via 10 string conditions. 27 types fall to a plain text area. 6 string bugs make modes unreachable.

---

## How the Routing Works

`getExecutionMode(interviewType)` in `CandidateInterviewRuntime.tsx` maps every type code to one of 10 modes:

```
includes('ai')           → ai         → text area
includes('assessment')   → assessment → radio group or text area
includes('video')        → video      → static placeholder shell
includes('panel')        → human      → waiting screen message
includes('hr')           → human      → waiting screen message
includes('leadership')   → human      → waiting screen message
includes('executive')    → human      → waiting screen message
=== 'group_discussion'   → group      → waiting room message
=== 'presentation_interview' → presentation → notes text area
=== 'role_play'          → role_play  → text area
=== 'portfolio_review'   → portfolio  → text area
=== 'mock_interview'     → mock       → text area
=== 'coding_interview'   → technical  → text area
=== 'system_design'      → technical  → text area
=== 'debugging_interview'→ technical  → text area
includes('technical')    → technical  → text area
(fallthrough)            → generic    → text area
```

---

## Full Registry Type Map

| # | Backend Code | Registry Name | Exec Mode (Registry) | Candidate Mode | Candidate UI | Status |
|---|---|---|---|---|---|---|
| 1 | `recruiter_screening` | Recruiter Screening | manual | `generic` | Text area | No dedicated panel |
| 2 | `ai_screening` | AI Screening | native | `ai` | Text area | No dedicated panel |
| 3 | `ai_technical` | AI Technical | native | `ai` | Text area | No dedicated panel |
| 4 | `ai_behavioral` | AI Behavioral | native | `ai` | Text area | No dedicated panel |
| 5 | `one_way_video` | One Way Video | native | `ai` | Text area | **BUG** — `one_way_video` matches `ai` check (line 71) before `video` check (line 73); video shell never renders |
| 6 | `phone_interview` | Phone Interview | manual | `generic` | Text area | No phone number / dial-in display |
| 7 | `async_text` | Async Text | async | `generic` | Text area | **BUG** — frontend checks `async_text_interview`; backend code is `async_text` |
| 8 | `async_audio` | Async Audio | async | `generic` | Text area | No audio recorder |
| 9 | `technical_interview` | Technical Interview | manual | `technical` | Text area | No dedicated panel |
| 10 | `coding_interview` | Coding Interview | native | `technical` | Text area | No code editor |
| 11 | `system_design` | System Design | manual | `technical` | Text area | No whiteboard / diagram tool |
| 12 | `take_home_assignment` | Take Home Assignment | async | `generic` | Text area + fake upload | Upload stores filename only — no actual file sent to backend |
| 13 | `debugging_interview` | Debugging Interview | manual | `technical` | Text area | No code execution |
| 14 | `whiteboard` | Whiteboard Interview | manual | `generic` | Text area | **BUG** — frontend checks `whiteboard_interview`; backend code is `whiteboard` |
| 15 | `technical_panel` | Technical Panel | manual | `human` | Waiting screen | No panel member names shown |
| 16 | `behavioral` | Behavioral Interview | manual | `generic` | Text area | No dedicated panel |
| 17 | `culture_fit` | Culture Fit | manual | `generic` | Text area | No dedicated panel |
| 18 | `hr_interview` | HR Interview | manual | `human` | Waiting screen | No dedicated panel |
| 19 | `leadership` | Leadership Interview | manual | `human` | Waiting screen | No dedicated panel |
| 20 | `executive` | Executive Interview | manual | `human` | Waiting screen | No dedicated panel |
| 21 | `hiring_manager` | Hiring Manager Interview | manual | `generic` | Text area | No dedicated panel |
| 22 | `panel` | Panel Interview | manual | `human` | Waiting screen | No interviewer names |
| 23 | `sequential` | Sequential Interview | manual | `generic` | Text area | No sequence/step indicator |
| 24 | `stakeholder` | Stakeholder Interview | manual | `generic` | Text area | No dedicated panel |
| 25 | `bar_raiser` | Bar Raiser | manual | `generic` | Text area | No dedicated panel |
| 26 | `final_round` | Final Round | manual | `generic` | Text area | No dedicated panel |
| 27 | `mcq_assessment` | MCQ Assessment | native | `assessment` | Radio group | Works if questions have options set |
| 28 | `aptitude` | Aptitude Assessment | native | `generic` | Text area | **BUG** — frontend checks `aptitude_test`; backend code is `aptitude` |
| 29 | `psychometric` | Psychometric Assessment | third_party | `generic` | Text area | No third-party embed |
| 30 | `cognitive` | Cognitive Assessment | third_party | `generic` | Text area | No third-party embed |
| 31 | `language` | Language Assessment | native | `generic` | Text area | No language test UI |
| 32 | `case_study` | Case Study | manual | `assessment` | Radio group or text area | No case document viewer |
| 33 | `role_play` | Role Play | manual | `role_play` | Text area | No scenario display |
| 34 | `work_sample` | Work Sample | external | `generic` | Text area | **BUG** — frontend checks `work_sample_test`; backend code is `work_sample` |
| 35 | `presentation` | Presentation Round | manual | `generic` | Text area | **BUG** — frontend checks `presentation_interview`; backend code is `presentation` |
| 36 | `portfolio_review` | Portfolio Review | manual | `portfolio` | Text area | No portfolio/link viewer |
| 37 | `group_discussion` | Group Discussion | manual | `group` | Waiting room message | No participant list |
| 38 | `assessment_center` | Assessment Center | third_party | `assessment` | Radio group or text area | No third-party embed |
| 39 | `mock` | Mock Interview | manual | `generic` | Text area | **BUG** — frontend checks `mock_interview`; backend code is `mock` |
| 40 | `campus` | Campus Interview | manual | `generic` | Text area | No dedicated panel |
| 41 | `walkin` | Walk-in Interview | manual | `generic` | Text area | No dedicated panel |
| 42 | `interview_cafe` | Interview Cafe | native | `generic` | Text area | No dedicated panel |
| 43 | `live_video` | Live Video Interview | native | `video` | Static placeholder shell | No actual video capture / WebRTC |

---

## Mode Reach Summary

| Mode | Renders | Types That Actually Reach It | Count |
|---|---|---|---|
| `ai` | Text area | ai_screening, ai_technical, ai_behavioral, one_way_video (bug) | 4 |
| `assessment` | Radio group or text area | mcq_assessment, assessment_center, case_study | 3 |
| `video` | Static placeholder shell | live_video | 1 |
| `human` | "Waiting screen" message | technical_panel, hr_interview, leadership, executive, panel | 5 |
| `group` | "Waiting room" message | group_discussion | 1 |
| `presentation` | Notes text area | **Nothing** — bug, never reached | 0 |
| `role_play` | Text area | role_play | 1 |
| `portfolio` | Text area | portfolio_review | 1 |
| `mock` | Text area | **Nothing** — bug, never reached | 0 |
| `technical` | Text area | technical_interview, coding_interview, system_design, debugging_interview, technical (legacy) | 5 |
| `generic` | Text area | **27 types** | 27 |

**27 of 44 types → plain text area.** 2 modes (`presentation`, `mock`) are unreachable due to string bugs.

---

## String Matching Bugs (6 Total)

All 6 are exact string mismatches between the backend registry code and the frontend `===` check:

| Backend Code | Frontend Checks For | Result |
|---|---|---|
| `one_way_video` | `=== 'one_way_video'` hits `ai` first (line 71 before line 73) | Falls to `ai` instead of `video` |
| `async_text` | `=== 'async_text_interview'` | Falls to `generic` |
| `whiteboard` | `=== 'whiteboard_interview'` | Falls to `generic` |
| `aptitude` | `=== 'aptitude_test'` | Falls to `generic` |
| `work_sample` | `=== 'work_sample_test'` | Falls to `generic` |
| `presentation` | `=== 'presentation_interview'` | Falls to `generic` |
| `mock` | `=== 'mock_interview'` | Falls to `generic` |

Fix location: `CandidateInterviewRuntime.tsx` lines 71–80.

---

## Types With No Candidate Panel At All (Need Purpose-Built UI)

These types have candidate-facing interaction requirements that a plain text area cannot satisfy:

| Type | What Candidate Actually Needs |
|---|---|
| `one_way_video` | Camera access, recording countdown, video upload |
| `async_audio` | Microphone access, audio recording, playback before submit |
| `coding_interview` | Code editor (syntax highlighting, language selection, run/test) |
| `system_design` | Whiteboard or diagram tool (draw.io embed, Excalidraw, etc.) |
| `debugging_interview` | Code viewer + fix area, ideally with execution |
| `take_home_assignment` | Real file upload to `/documents/`, download link for brief |
| `live_video` | WebRTC video room or embedded meeting (Jitsi, Daily.co, etc.) |
| `phone_interview` | Dial-in number, PIN, call instructions display |
| `psychometric` | Third-party iframe embed (e.g., SHL, Hogan, TalentQ) |
| `cognitive` | Third-party iframe embed |
| `assessment_center` | Third-party iframe embed |
| `language` | Speaking + writing test UI, audio prompt playback |
| `presentation` | Slide upload, presentation notes, video delivery option |
| `case_study` | Case document viewer / PDF embed, structured answer form |
| `role_play` | Scenario description display, structured response form |
| `group_discussion` | Participant list, moderator info, join link prominent |
| `sequential` | Step indicator — which round is this, how many total |
| `portfolio_review` | Portfolio link input or file viewer |
| `mcq_assessment` | Timer per question, no back-navigation (if configured) |

---

## Fix Priority

### P1 — String Bugs (5-minute fixes each)

Change the `getExecutionMode` function in `CandidateInterviewRuntime.tsx`:

| Bug | Fix |
|---|---|
| `one_way_video` falls to `ai` | Move `one_way_video` check to `video` condition only (remove from line 71) |
| `async_text` no match | Change `'async_text_interview'` → `'async_text'` |
| `whiteboard` no match | Change `'whiteboard_interview'` → `'whiteboard'` |
| `aptitude` no match | Change `'aptitude_test'` → `'aptitude'` |
| `work_sample` no match | Change `'work_sample_test'` → `'work_sample'` |
| `presentation` no match | Change `'presentation_interview'` → `'presentation'` |
| `mock` no match | Change `'mock_interview'` → `'mock'` |

### P2 — Native Type Panels (Require Build)

| Priority | Type | Effort |
|---|---|---|
| High | `one_way_video` | Camera + recording + upload |
| High | `coding_interview` | Code editor (Monaco/CodeMirror) |
| High | `live_video` | WebRTC or embedded meeting room |
| Medium | `async_audio` | Audio recorder |
| Medium | `take_home_assignment` | Real file upload |
| Medium | `mcq_assessment` | Timer, no-back enforcement |
| Medium | `system_design` | Whiteboard embed |

### P3 — Manual Type Enhancements (Display-Only)

| Priority | Type | What to Add |
|---|---|---|
| Medium | `phone_interview` | Dial-in number, PIN display |
| Medium | `sequential` | Round N of M indicator |
| Medium | `panel` / `technical_panel` | Interviewer names from interview panelist list |
| Medium | `case_study` | Case brief PDF viewer |
| Low | `role_play` | Scenario card display |
| Low | `group_discussion` | Participant count, moderator name |
| Low | `portfolio_review` | Portfolio link input field |
| Low | `psychometric` / `cognitive` / `assessment_center` | Third-party iframe placeholder with redirect link |

### P4 — Third-Party Integrations (Deferred)

`psychometric`, `cognitive`, `assessment_center` — require vendor contracts and iframe / redirect integration. Not buildable without provider config.
