# ICC-CANDIDATE-RUNTIME-ENGINE-01 QA

## Scope
Candidate-facing interview runtime system with dashboard, instructions, runtime execution page, join flow, answer submission, status tracking, and security shell preparation.

## Embedded QA Checks

### 1) Candidate Dashboard Loads
- Endpoint: `GET /api/v1/candidate/interviews/`
- Verified response includes:
  - `upcoming_interviews`
  - `pending_interviews`
  - `completed_interviews`
  - `missed_interviews`

Result: PASS

### 2) Interview Opens
- Endpoints:
  - `GET /api/v1/candidate/interviews/{id}/instructions/`
  - `GET /api/v1/candidate/interviews/{id}/runtime/`
- Verified instructions and question payload load for candidate runtime.

Result: PASS

### 3) Join Works
- Endpoint: `POST /api/v1/candidate/interviews/{id}/start/`
- Verified scheduled interview moves to `in_progress` and runtime starts.
- Meeting/external links are exposed on runtime page when available.

Result: PASS

### 4) Status Updates
- Endpoints:
  - `POST /api/v1/candidate/interviews/{id}/submit-answer/`
  - `POST /api/v1/candidate/interviews/{id}/complete/`
  - `GET /api/v1/candidate/interviews/{id}/status/`
- Verified answer submit and completion update status and tracking payload.

Result: PASS

### 5) Security Shell Prepared
- Verified metadata-based runtime shell supports:
  - token-based access shell
  - time-based access window shell
  - single-attempt shell (`attempts_used`)

Result: PASS

### 6) Stability
- No backend 500 for invalid runtime interview lookup (returns 404).
- Candidate interview dashboard/instructions/runtime/status UI routes load without console crash.

Result: PASS

## Automated Validation Executed
- `python3 manage.py test apps.interviews.tests.test_candidate_runtime_engine apps.interviews.tests.test_integration_engine apps.interviews.tests.test_decision_engine -v 2`
- `npm run -s build`

Both completed successfully.
