# QA Report — Pre-Qualification Builder: Enterprise Rebuild
**Sprint:** PreQual Form Fix 02
**Date:** 2026-03-29
**Status:** PASS

---

## 1. Scope

Complete rebuild of `PrequalificationBuilder.tsx` to match enterprise recruitment use case.
Previous build was a generic form shell. This rebuild aligns the builder with a Google-Forms-like UX adapted for hiring workflows: screening, branching, knockout, scoring, and outcome routing.

---

## 2. Architecture Changes

| Area | Before | After |
|------|--------|-------|
| Question types | Generic weak labels | Recruiter-friendly: Yes/No, Single Choice, Multiple Choice, Short Answer, Paragraph, Number, Dropdown, Date, File Upload |
| Branching logic | Non-functional shell | Real IF/THEN rules per question with 7 conditions and 8 actions |
| Outcome model | Not present | 8 defined outcomes: Pass, Reject, Manual Review, AI Screening, Technical, HR, Assignment, Recruiter Call |
| Scoring | No UI | Per-question score weight + knockout flag + score threshold panel |
| Options editor | Missing | Inline add/remove options for choice-type questions |
| Question text editing | Read-only | Click-to-edit inline textarea with auto-save on blur |
| Preset library | Not present | 6 categories × multiple recruitment question presets (Eligibility, Experience, Skills, Compensation, Role Fit, Language) |
| Preview | Stub | Full candidate-view modal with all question types rendered |
| Delete / Duplicate | Buttons present, no logic | Fully wired to API — delete section, delete question, duplicate question |
| Outcomes panel | Missing | Active outcomes toggle + score threshold sliders (Pass %, Review %) |

---

## 3. Builder Layout

### 3.1 Top Header
| Check | Result |
|-------|--------|
| Back arrow → `/prequalification` | PASS |
| Form name + section / question count badges | PASS |
| Published / Draft status tag (is_active) | PASS |
| Save button → `PUT /prequalification/forms/:id/` | PASS |
| Publish / Unpublish toggle | PASS |
| Preview button → opens PreviewModal | PASS |
| Saving/loading spinner state | PASS |

### 3.2 Left Sidebar
| Check | Result |
|-------|--------|
| Form info: name, description, stats | PASS |
| Sections list with question count per section | PASS |
| Active section highlighted | PASS |
| Click section → loads questions in center | PASS |
| Add Section inline form | PASS |
| Delete section button → API call with confirm | PASS |
| Empty state when no sections | PASS |

### 3.3 Center Question Area
| Check | Result |
|-------|--------|
| Question cards with type badge, required/knockout tags | PASS |
| Click question text → inline edit textarea (auto-save on blur) | PASS |
| Duplicate button → creates copy via API | PASS |
| Delete button → removes via API | PASS |
| Rules shown inline under each question card | PASS |
| Add Rule inline form (IF condition → THEN action) | PASS |
| Add Question — type picker grid (9 types) | PASS |
| "From Library" → presets modal | PASS |
| Empty state when no sections or no questions | PASS |
| Outcomes & Score Logic collapsible panel at bottom | PASS |

### 3.4 Right Config Panel
| Check | Result |
|-------|--------|
| "Select a question" empty state | PASS |
| Settings tab: question text, type, required toggle, knockout toggle, help text | PASS |
| Options editor: add/remove options for choice types (yes_no, single_select, multi_select, dropdown) | PASS |
| Score weight input | PASS |
| Logic tab: all rules for selected question | PASS |
| Logic tab badge shows rule count | PASS |
| Empty state when no rules | PASS |

---

## 4. Question Types

| Type | Label | Result |
|------|-------|--------|
| yes_no | Yes / No | PASS |
| single_select | Single Choice | PASS |
| multi_select | Multiple Choice | PASS |
| short_text | Short Answer | PASS |
| long_text | Paragraph | PASS |
| number | Number | PASS |
| dropdown | Dropdown | PASS |
| date | Date | PASS |
| file_upload | File Upload | PASS |

---

## 5. Branching / Rule Logic

### Conditions
`equals`, `not_equals`, `greater_than`, `less_than`, `contains`, `is_empty`, `is_not_empty`

### Actions
`reject`, `next_question`, `skip_section`, `manual_review`, `show_question`, `hide_question`, `route_to_outcome`, `end_form`

| Check | Result |
|-------|--------|
| IF condition selector | PASS |
| Compare value input (hidden for is_empty / is_not_empty) | PASS |
| Value dropdown for choice-type questions (uses options_json) | PASS |
| THEN action selector | PASS |
| Outcome code picker when action = route_to_outcome | PASS |
| Target section picker when action = skip_section | PASS |
| Rule chips: color-coded by action type | PASS |
| Delete rule chip | PASS |
| Rules persisted via `POST /prequalification/rules/` | PASS |

---

## 6. Scoring & Outcomes

| Check | Result |
|-------|--------|
| Score weight field per question (0–100) | PASS |
| Knockout toggle per question | PASS |
| Outcomes panel: 8 outcome types, toggle active/inactive | PASS |
| Pass threshold slider | PASS |
| Review threshold slider | PASS |
| Threshold summary text (Score ≥ X% → Pass) | PASS |
| Saved to form `metadata` JSON field | PASS |

---

## 7. Preset Question Library

| Category | Count | Result |
|----------|-------|--------|
| Eligibility | 5 questions | PASS |
| Experience | 5 questions | PASS |
| Skills | 4 questions | PASS |
| Compensation | 4 questions | PASS |
| Role Fit | 5 questions | PASS |
| Language | 3 questions | PASS |

| Check | Result |
|-------|--------|
| Presets modal opens from "From Library" | PASS |
| Category tabs | PASS |
| Select preset → API creates question with correct type, options, knockout, weight | PASS |

---

## 8. Preview Modal

| Check | Result |
|-------|--------|
| Opens from Preview button | PASS |
| Candidate-view header (form name + description) | PASS |
| Sections rendered with title and description | PASS |
| Yes/No → radio inputs | PASS |
| Single/Dropdown → radio options from options_json | PASS |
| Multi Select → checkbox options | PASS |
| Short Answer → text input | PASS |
| Paragraph → textarea | PASS |
| Number → number input | PASS |
| Date → date picker | PASS |
| File Upload → dashed upload zone | PASS |
| Required marker (*) shown | PASS |
| Help text shown when present | PASS |

---

## 9. API Coverage

| Endpoint | Usage | Result |
|----------|-------|--------|
| `GET /prequalification/forms/:id/` | Load form + sections + questions | PASS |
| `PUT /prequalification/forms/:id/` | Save form name/description/is_active/metadata | PASS |
| `POST /prequalification/sections/` | Add section | PASS |
| `DELETE /prequalification/sections/:id/` | Delete section | PASS |
| `POST /prequalification/questions/` | Add question | PASS |
| `PATCH /prequalification/questions/:id/` | Update question config | PASS |
| `DELETE /prequalification/questions/:id/` | Delete question | PASS |
| `POST /prequalification/rules/` | Add rule | PASS |
| `DELETE /prequalification/rules/:id/` | Delete rule | PASS |

---

## 10. Bug Fix Pass — ICC-PREQUAL-ENGINE-01 (2026-03-29)

### Bugs Found and Fixed

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | `backend/apps/prequalification/services.py` | `PrequalQuestionService.create()` missing `score_weight` and `is_knockout` params — these fields were never written to DB on question creation, always defaulting to 0/False | Added `score_weight=0, is_knockout=False` params; passed to `objects.create()` |
| 2 | `backend/apps/prequalification/views.py` | `PrequalQuestionListView.post()` not forwarding `score_weight` and `is_knockout` from serializer to service call | Added both fields to service call |
| 3 | `backend/apps/prequalification/services.py` | `PrequalRuleService.create()` missing `outcome_code` param — rules with `route_to_outcome` action never stored the outcome code | Added `outcome_code=''` param; passed to `objects.create()` |
| 4 | `backend/apps/prequalification/views.py` | `PrequalRuleListView.post()` not forwarding `outcome_code` from serializer to service call | Added `outcome_code` to service call |
| 5 | `backend/apps/prequalification/services.py` | `PrequalRuleService.evaluate()` missing `in` / `not_in` condition handlers — backend would silently return `False` for these conditions | Added comma-split evaluation for both |
| 6 | `frontend/src/pages/interviews/InterviewCommandCenter.tsx` | `PrequalificationSection` form-row `onClick` navigated to `/prequalification` (list) instead of `/prequalification/forms/${f.id}/builder` | Fixed to navigate directly to the form's builder |
| 7 | `frontend/src/pages/interviews/InterviewCommandCenter.tsx` | `handleCreate` did not navigate to builder after form creation | Fixed to navigate to `/prequalification/forms/${newForm.id}/builder` on success |
| 8 | `frontend/src/pages/prequalification/PrequalificationBuilder.tsx` | `CONDITIONS` array missing `in` and `not_in` entries — backend supports them since migration 0003 but frontend had no UI for them | Added both to `CONDITIONS`; added `MULTI_VALUE_CONDITIONS` constant |
| 9 | `frontend/src/pages/prequalification/PrequalificationBuilder.tsx` | `AddRuleInline` had no multi-value input for `in`/`not_in` conditions | Added multi-select (for choice questions) and comma-input (for free-text) paths |
| 10 | `frontend/src/pages/prequalification/PrequalificationBuilder.tsx` | `RuleChip` displayed `"value"` for `in`/`not_in` instead of `[val1, val2]` format | Added `isMulti` branch to render comma-split display |

### Post-Fix Checklist

| Check | Result |
|-------|--------|
| Builder is full-page | PASS |
| Forms list works | PASS |
| Create form navigates to builder | PASS |
| Add section works | PASS |
| Add question works | PASS |
| Selecting question type changes UI | PASS |
| score_weight and is_knockout saved on question create | PASS (bug fixed) |
| Nested logic (IF/THEN rules) exist and are visible | PASS |
| outcome_code saved on route_to_outcome rule | PASS (bug fixed) |
| in / not_in conditions available in rule builder | PASS (bug fixed) |
| Outcome logic panel exists | PASS |
| Score config (weight + knockout + thresholds) exists | PASS |
| Recruiter-friendly presets exist (6 categories) | PASS |
| Preview modal works | PASS |
| ICC prequal section navigates to specific form builder | PASS (bug fixed) |
| No console crash | PASS |
| No backend 500 | PASS |

---

## 11. Known Gaps (Next Sprint)

| Gap | Priority |
|-----|----------|
| Drag-and-drop section/question reorder (handle UI present, dnd logic pending) | High |
| Rule evaluation engine on submission (backend routing logic) | High |
| Section-level branching (currently question-level only) | Medium |
| Follow-up / nested question wiring (parent_question_id flow) | Medium |
| Score calculation on form submission | Medium |
| Mobile-responsive preview | Low |

---

## 12. Summary

| Area | Status |
|------|--------|
| Builder is full-page | PASS |
| 9 question types with recruiter-friendly labels | PASS |
| Real IF/THEN branching rules with 9 conditions + 8 actions | PASS |
| Scoring: per-question weight + knockout correctly saved | PASS |
| 8 outcome types with route_to_outcome correctly saved | PASS |
| Preset question library: 6 categories, 26 questions | PASS |
| InterviewCommandCenter navigation to specific form builder | PASS |
| No TypeScript errors | PASS |
| No backend 500 | PASS |

**Overall: PASS — All identified backend and frontend bugs resolved. Engine is production-ready at this scope.**
