# Implemented Flows

## Candidate Registration & Login
### Status
PARTIAL / UNVERIFIED (Path Mismatch)
### Backend Evidence
- `backend/apps/accounts/urls.py`
- Endpoints: `/accounts/login/`, `/accounts/register/candidate/`, `/accounts/onboarding/complete/`
### Frontend Evidence
- `frontend/src/api/auth.ts` calling `/auth/login/`, `/auth/register/candidate/`
- Pages: `auth/Login.tsx`, `auth/RegisterCandidate.tsx`
### Current Test Coverage
- pytest: `apps/accounts/tests/test_onboarding.py`
### Main Gaps
- Route mismatch (`/auth/` vs `/accounts/`).
- No e2e tests.
### Recommended Next Test
- Test end-to-end registration API using schemathesis or direct pytest.

## Candidate CRM & Management
### Status
IMPLEMENTED
### Backend Evidence
- `backend/apps/candidates/urls.py`
- Endpoints: `/candidates/`, `/candidates/<uuid:pk>/`, `/candidates/<uuid:pk>/notes/`
### Frontend Evidence
- `frontend/src/api/candidates.ts` calling `/candidates/`
- Pages: `candidates/CandidatesList.tsx`, `candidates/CandidateDetail.tsx`
### Current Test Coverage
- none
### Main Gaps
- Completely untested backend logic.
### Recommended Next Test
- Pytest API tests for creating and listing candidates.

## Job Requisitions & Postings
### Status
IMPLEMENTED
### Backend Evidence
- `backend/apps/jobs/urls.py`
- Endpoints: `/jobs/requisitions/`, `/jobs/postings/`
### Frontend Evidence
- `frontend/src/api/jobs.ts` calling `/jobs/requisitions/`, `/jobs/postings/`
- Pages: `jobs/JobsList.tsx`, `jobs/JobDetail.tsx`, `jobs/JobCreate.tsx`
### Current Test Coverage
- none
### Main Gaps
- Missing validation tests for stage transitions.
### Recommended Next Test
- Pytest API test for creating a requisition and publishing a job.

## Agency Relationships
### Status
IMPLEMENTED
### Backend Evidence
- `backend/apps/agencies/urls.py`
- Endpoints: `/agencies/relationships/`, `/agencies/assignments/`
### Frontend Evidence
- `frontend/src/api/agencies.ts` calling `/agencies/relationships/`
- Pages: `agencies/AgenciesList.tsx`, `agency/AgencyDashboard.tsx`
### Current Test Coverage
- none
### Main Gaps
- Untested assignment logic.
### Recommended Next Test
- Pytest API test for agency invitations and assignments.
