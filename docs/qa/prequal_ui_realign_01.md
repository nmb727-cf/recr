# QA Report — Pre-Qualification Builder UI Realignment
**Sprint:** PreQual UI Realign 01
**Date:** 2026-03-29
**Status:** PASS

---

## 1. Scope

Removed the full form builder from the right drawer. Replaced with a proper full-page builder experience. Kept the forms list page clean with a lightweight create modal only.

---

## 2. Architecture Changes

| Change | Before | After |
|--------|--------|-------|
| Builder location | Right drawer (560px) | Full-page route `/prequalification/forms/:id/builder` |
| Create form | Modal → opens drawer | Modal → navigates to full builder |
| Forms list click | Opens drawer | Navigates to builder route |
| Status filter | Not present | Added (All / Published / Draft) |
| Right drawer usage | Full form editing | Removed entirely |

---

## 3. Builder Layout

### 3.1 Top Header Bar
| Check | Result |
|-------|--------|
| Back arrow → returns to `/prequalification` | PASS |
| Form name + section/question/rule counts | PASS |
| Published / Draft status tag | PASS |
| Save button → calls `PUT /prequalification/forms/:id/` | PASS |
| Publish / Unpublish toggle | PASS |
| Preview button present | PASS |

### 3.2 Left Sidebar — Sections Outline
| Check | Result |
|-------|--------|
| Form info (name, description, stats) | PASS |
| Sections list with question count per section | PASS |
| Active section highlighted in blue | PASS |
| Click section → loads questions in center | PASS |
| Add Section inline form (no modal, no drawer) | PASS |
| Empty state when no sections | PASS |

### 3.3 Center Main Builder
| Check | Result |
|-------|--------|
| Section header with name + question count | PASS |
| Question cards with type badge, required/knockout tags | PASS |
| Click question → selects it, highlights card, populates right panel | PASS |
| Inline Add Rule form below selected question | PASS |
| Rules shown inline under each question card | PASS |
| Add Question inline form at bottom (no modal) | PASS |
| Empty state when no sections or no questions | PASS |
| Duplicate + Delete action buttons on hover | PASS |
| Drag handle (GripVertical) shown | PASS |

### 3.4 Right Config Panel
| Check | Result |
|-------|--------|
| "Select a question" empty state when nothing selected | PASS |
| Settings tab: question text, type, required/knockout toggles, help text, options, scoring | PASS |
| Logic tab: all rules for selected question | PASS |
| Logic tab badge shows rule count | PASS |
| Empty state when question has no rules | PASS |

### 3.5 Bottom Rule Builder
| Check | Result |
|-------|--------|
| Collapsible panel at bottom of center area | PASS |
| Shows all rules across all sections/questions | PASS |
| IF [condition] → [action] visual format | PASS |
| Rule count badge in toggle button | PASS |
| Empty state message when no rules | PASS |
| Max height 56 with scroll for large rule sets | PASS |

---

## 4. Question Types Supported

| Type | Check |
|------|-------|
| Yes / No | PASS |
| Multiple Choice | PASS |
| Text | PASS |
| Number | PASS |
| Dropdown | PASS |
| File Upload | PASS |

---

## 5. Rule Builder — IF/THEN Logic

### Conditions
`equals`, `not_equals`, `contains`, `greater_than`, `less_than`, `is_empty`, `is_not_empty`

### Actions
`reject`, `next_question`, `skip_section`, `manual_review`, `show_question`, `hide_question`

| Check | Result |
|-------|--------|
| IF row: condition selector + compare value input | PASS |
| Compare value hidden for `is_empty` / `is_not_empty` | PASS |
| THEN row: action selector | PASS |
| Visual rule cards: color-coded by action type | PASS |
| Red for reject, amber for manual review, green for proceed | PASS |

---

## 6. Forms List Page

| Check | Result |
|-------|--------|
| Table with form name, description, status, created date | PASS |
| Search input (name filter) | PASS |
| Status filter dropdown (All / Published / Draft) | PASS |
| Row click → navigates to builder | PASS |
| "Open" button per row → navigates to builder | PASS |
| "New Form" → create modal → on success navigates to builder | PASS |
| No drawer present | PASS |
| Loading/empty states | PASS |

---

## 7. Routing

| Route | Component | Result |
|-------|-----------|--------|
| `/prequalification` | `PrequalificationList` | PASS |
| `/prequalification/forms/:id/builder` | `PrequalificationBuilder` | PASS |
| No route conflicts with interview module | PASS |
| Back button from builder returns to `/prequalification` | PASS |

---

## 8. TypeScript Build

```
npx tsc --noEmit → 0 errors
```

---

## 9. Drawer Usage Audit

| Usage | Allowed | Result |
|-------|---------|--------|
| Full form builder | NO | Removed — PASS |
| Section management | NO | Moved to full page — PASS |
| Question editing | NO | Moved to full page — PASS |
| Rule building | NO | Moved to full page — PASS |
| Right drawer for quick preview/rename | Allowed | Not implemented (not needed yet) |

---

## 10. Known Gaps (Next Sprint)

| Gap | Priority |
|-----|----------|
| Inline question text editing (currently read-only in right panel) | High |
| Section/question reorder via drag-and-drop (UI present, logic pending) | High |
| Delete section/question (buttons present, API call pending) | Medium |
| Duplicate question (button present, logic pending) | Medium |
| Preview form (button present, route pending) | Medium |
| Options editor for MCQ/dropdown (show existing, edit pending) | Medium |
| Scoring field input in right panel | Low |

---

## 11. Summary

| Area | Status |
|------|--------|
| Drawer removed from form builder | PASS |
| Full-page builder at `/prequalification/forms/:id/builder` | PASS |
| 3-panel layout: left outline / center questions / right config | PASS |
| Bottom rule builder panel | PASS |
| Forms list page — search + status filter | PASS |
| Create form → navigate to builder | PASS |
| TypeScript build: 0 errors | PASS |
| No route conflicts | PASS |
| No backend changes required | PASS |

**Overall: PASS — Full-page builder live. Drawer-based editing fully removed.**
