# ICC-DECISION-ENGINE-01 QA

## Scope
Centralized Interview Decision Engine with extended decision types, source-aware decisioning, manual/auto/conditional logic, multi-interviewer aggregation, override, and decision history.

## Embedded QA Checks

### 1) Decision Create Works
- Endpoint: `POST /api/v1/interviews/{id}/decision/`
- Verified decision persisted with source/mode/notes.

Result: PASS

### 2) Override Works
- Endpoint: `POST /api/v1/interviews/{id}/decision/` with `is_override=true`
- Verified override flags, reason, and previous decision captured.

Result: PASS

### 3) History Works
- Endpoint: `GET /api/v1/interviews/{id}/decision/history/`
- Verified chronological decision history rows with actor/source/override metadata.

Result: PASS

### 4) Multi Interviewer Works
- Endpoint: `POST /api/v1/interviews/{id}/decision/evaluate/`
- Verified majority + weighted aggregation and conditional threshold decisioning.
- Hiring manager override input supported in evaluation payload.

Result: PASS

### 5) Stability
- No backend 500 in create/override/history/evaluate flows.
- Decision panel UI loads and submits without runtime crash.

Result: PASS

## Automated Validation Executed
- `python3 manage.py test apps.interviews.tests.test_decision_engine apps.interviews.tests.test_scorecard_engine apps.interviews.tests.test_scheduling_engine apps.interviews.tests.test_interview_types_engine -v 2`
- `npm run -s build`

Both completed successfully.
