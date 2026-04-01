# ICC-SCORECARD-ENGINE-01 QA

## Scope
Interview Scorecard Builder, Interview Kit loading, structured feedback submission, and multi-interviewer panel aggregation.

## Environment
- Backend: Django API (`/api/v1/interviews/...`)
- Frontend: React app interview pages

## Embedded QA Checks

### 1) Scorecard Create Works
- Endpoint: `POST /api/v1/interviews/scorecards/templates/`
- Payload includes: `name`, `description`, `interview_type`, `attributes[]`
- Expected:
  - `201` response
  - scorecard persisted under authenticated user tenant
  - attributes persisted with weight/rating_type/required/order

Result: PASS

### 2) Interview Kit Loads
- Endpoint: `GET /api/v1/interviews/{id}/kit/`
- Expected payload sections:
  - `candidate`
  - `job`
  - `resume_url`
  - `instructions`
  - `questions`
  - `scorecard`
  - `panelists`
  - `feedback`
  - `panel_decision`

Result: PASS

### 3) Feedback Submit Works
- Endpoint: `POST /api/v1/interviews/{id}/structured-feedback/`
- Payload supports:
  - `score`
  - `notes`
  - `recommendation` (`hire|reject|hold|next_round`)
  - `scorecard_ratings` (JSON)
- Expected:
  - `200` response
  - upserted interviewer feedback record
  - returned `panel_decision`

Result: PASS

### 4) Multi Interviewer Works
- Two different interviewers submit structured feedback on same interview.
- Endpoint: `GET /api/v1/interviews/{id}/panel-decision/`
- Expected:
  - recommendation counts aggregated
  - combined recommendation resolved by top count (tie breaks deterministic by key sort)
  - average score computed from non-null scores

Result: PASS

### 5) Stability Checks
- No backend `500` during create/load/submit/panel-decision flows.
- Frontend build succeeds and renders new screens:
  - `/interviews/scorecards`
  - `/interviews/:id/kit`
  - `/interviews/:id/feedback`

Result: PASS

## Automated Validation Executed
- `python3 manage.py test apps.interviews.tests.test_scorecard_engine -v 2`
- `npm run -s build`

Both completed successfully.
