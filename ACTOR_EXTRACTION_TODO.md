# ACTOR EXTRACTION TODO

Preserve all currently working company, agency, and candidate behavior; if a mixed file supports multiple actors, split it without dropping any supported path.

1.  **Separate Agency Actor (Backend)**
    *   Move `backend/apps/agencies/` (Agency-facing parts) -> `backend/apps/actors/agency/`
    *   Move `backend/apps/agency_candidates/` -> `backend/apps/actors/agency/`
    *   Move `backend/apps/talent_pools/` -> `backend/apps/actors/agency/`
    *   *Note: Extract relationship logic into `bridge/` if needed.*

2.  **Separate Company Actor (Backend)**
    *   Move `backend/apps/organisations/` -> `backend/apps/actors/company/`
    *   Move `backend/apps/recruiter_workspace/` -> `backend/apps/actors/company/`
    *   Split `backend/apps/jobs/views.py` (Move recruiter-facing views) -> `backend/apps/actors/company/api/`

3.  **Separate Candidate Actor (Backend)**
    *   Move `backend/apps/passport/` -> `backend/apps/actors/candidate/`
    *   Split `backend/apps/candidates/views.py` (Move candidate-facing self-service) -> `backend/apps/actors/candidate/api/`

4.  **Frontend Actor Extraction**
    *   Group actor-specific pages under `frontend/src/actors/`
    *   Group actor-specific components and hooks
    *   Isolate actor-specific routes in a central configuration

5.  **Isolate Mixed Actor Files**
    *   Create thin compatibility wrappers for re-exports to maintain old paths until Phase 7.
    *   Use direct imports in new locations.
