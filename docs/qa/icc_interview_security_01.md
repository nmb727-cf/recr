# ICC-INTERVIEW-SECURITY-ENGINE-01 QA

## Scope
Interview runtime security layer for candidate access: token validation, time window enforcement, single-attempt control, session lock handling, anti-cheat shell events, and attempt tracking.

## Embedded QA Checks

### 1) Token Validation Works
- Runtime/start endpoints require valid interview token.
- Invalid token returns controlled 403 with security error code (`token_invalid`).

Result: PASS

### 2) Expiry Works
- Expired token/time window returns controlled 410 with security code (`token_expired`).

Result: PASS

### 3) Attempt Tracking Works
- Tracks attempt lifecycle in runtime metadata:
  - attempt start time
  - attempt end time
  - duration seconds
  - attempt status
  - attempt history entries

Result: PASS

### 4) Session Lock Works
- Active session is locked by `active_session_id`.
- Different session re-entry is blocked with 409 (`session_locked`).
- Same session rejoin is allowed and rejoin count is tracked.

Result: PASS

### 5) Anti-Cheat Shell Prepared
- Shell event endpoint records:
  - tab switch events
  - copy/paste events
  - multiple-window events
- Counters persist in runtime security metadata.

Result: PASS

### 6) UI Security State Handling
- Added blocked state page.
- Added expired link page.
- Runtime page redirects to these states based on backend security error codes.

Result: PASS

### 7) Stability
- No backend 500 in security checks and runtime transitions.
- Frontend build successful; no console crash in security state flows.

Result: PASS

## Automated Validation Executed
- `python3 manage.py test apps.interviews.tests.test_security_engine apps.interviews.tests.test_candidate_runtime_engine apps.interviews.tests.test_decision_engine -v 2`
- `npm run -s build`

Both completed successfully.
