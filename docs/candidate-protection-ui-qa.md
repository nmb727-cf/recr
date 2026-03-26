# QA SPEC — Candidate Protection UI
# Feature ID: CANDIDATE-PROTECTION-UI-011

## Goal
Verify that Candidate Protection UI is fully visible and correctly enforced for agency-protected candidates.

## Scope
Only test these areas:

- Candidate Database
- Candidate Quick View
- Candidate Full View
- Candidate Workbench
- Candidate API filter support for protection status

Do not test unrelated job detail build issues in this run.

---

## Preconditions

Test data required:

1. Company user account with access to candidate database
2. Agency user account able to submit candidates
3. One active agency-company relationship with retention enabled
4. One candidate submitted by agency to company with active protection
5. One normal non-protected candidate

Expected agreement setup:
- retention_enabled = true
- retention_days has valid value
- retention scope has valid value

---

## Backend / API Checks

### API Check 1 — Candidate database filter
Open candidate database API using:
- protection_status=protected
- protection_status=not_protected

Expected:
- protected filter returns only active protected candidates
- not_protected filter excludes active protected candidates

### API Check 2 — Candidate protection fields
For protected candidate response, verify fields exist and are populated:

- is_agency_protected
- protected_until
- protection_scope

Expected:
- is_agency_protected = true
- protected_until has valid date
- protection_scope has valid value

### API Check 3 — Non-protected candidate response
Expected:
- protected state absent or false
- no misleading protection metadata shown

---

## Frontend Checks — Candidate Database

### UI Check 1 — Protected candidate visible in database
Expected:
- Agency Protected badge visible
- Protected Until visible in row/card/metadata area
- Scope visible in compact form where implemented

### UI Check 2 — Non-protected candidate
Expected:
- no Agency Protected badge
- no protected metadata

### UI Check 3 — Multiple view modes
Verify in all implemented views:
- list view
- compact view
- card view

Expected:
- protected state visible consistently in each supported view

---

## Frontend Checks — Protection Filter

### UI Check 4 — Filter options
Expected filter options:
- All
- Agency Protected
- Not Protected

### UI Check 5 — Filter behavior
Expected:
- Agency Protected shows protected candidates only
- Not Protected excludes protected candidates
- All shows both correctly

---

## Frontend Checks — Quick View / Full View / Workbench

### UI Check 6 — Quick View
Expected Protection Status block includes:
- Status
- Protected Until
- Scope
- short restriction note

### UI Check 7 — Full View
Expected Protection Status block includes:
- Status
- Protected Until
- Scope
- short restriction note

### UI Check 8 — Workbench
Expected:
- protection state visible
- same protection fields rendered consistently

---

## Action Lock / Restricted UX Checks

### UI Check 9 — Bulk export blocked
Select at least one protected candidate and try bulk export.

Expected:
- export is visibly disabled or blocked
- clear reason shown
- user sees protection explanation

### UI Check 10 — Submit to job modal
Open submit-to-job for protected candidate.

Expected:
- protection context shown before action
- if action is not allowed by backend, backend message is surfaced clearly
- no generic silent failure

### UI Check 11 — Non-protected candidate action behavior
Expected:
- existing behavior unchanged
- no accidental restriction shown

---

## Safety / Regression Checks

### Regression Check 1
Verify non-protected candidate flows still work.

### Regression Check 2
Verify no unrelated candidate module screens are broken.

### Regression Check 3
Ignore unrelated pre-existing build issue:
- src/pages/jobs/JobDetail.tsx:318

This issue must be recorded as external to this feature if encountered.

---

## Pass Criteria

Mark PASS only if all below are true:

- protected badge visible
- protected until visible
- scope visible
- protection filter works
- bulk export blocked visually
- backend rejection messages surface correctly
- non-protected flows remain unchanged

---

## Report Format Required

Return report in this exact structure:

### Result
PASS / FAIL / PASS WITH KNOWN EXTERNAL BLOCKER

### Feature
Candidate Protection UI

### Tested Areas
- Candidate Database
- Candidate Quick View
- Candidate Full View
- Candidate Workbench
- Candidate API Filter

### Passed Checks
- ...

### Failed Checks
- ...

### Screens / Evidence
- ...

### Backend/API Findings
- ...

### Frontend Findings
- ...

### Regression Findings
- ...

### Known External Blockers
- src/pages/jobs/JobDetail.tsx:318 (only if encountered, and clearly marked unrelated)

### Final Verdict
- Complete
- Partial
- Needs Fix