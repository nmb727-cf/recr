# Company Phase 4 — Onboarding + Handoff

## Onboarding Creation
Status: Implemented

Notes:
- Onboarding record uses existing `hdc.JoiningCase` and now includes `candidate_id`, `job_id`, `offer_id`, `assigned_hr_id`.
- Offer acceptance callback (`/api/v1/company/external/candidate-offer-response/`) now auto-initializes onboarding case when response is `accepted`.
- Default checklist + document/handoff metadata are seeded.

## Checklist
Status: Implemented

Notes:
- Default checklist seeded with:
  - documents received
  - background verification
  - IT provisioning
  - HR documentation
  - joining confirmation
- Added API actions on joining case:
  - `GET /api/v1/hdc/joining/{id}/checklist/`
  - `POST /api/v1/hdc/joining/{id}/upsert_checklist_item/`

## Document Collection
Status: Implemented

Notes:
- Added external endpoint:
  - `POST /api/v1/company/external/candidate-document-uploaded/`
- Payload supported:
  - `onboarding_id`, `document_type`, `document_status`, `notes`
- Updates onboarding documents metadata and checklist progression.
- Triggers workflow resume event (`document_signed`) for waiting document/signature stages.

## Handoff
Status: Implemented

Notes:
- Added external endpoint:
  - `POST /api/v1/company/external/hrms-handoff/`
- Payload supported:
  - `onboarding_id`, `status` (`acknowledged` | `rejected`), `notes`
- On acknowledged: onboarding status becomes `handed_off`, workflow resume event `hrms_handoff_acknowledged` emitted.
- On rejected: onboarding remains actionable (`completed`) with event `hrms_handoff_rejected`.
- Added company-side handoff payload preparation API:
  - `POST /api/v1/hdc/joining/{id}/prepare_handoff/`

## Workflow Integration
Status: Implemented

Notes:
- Workflow callback tests pass for:
  - candidate offer response (including onboarding creation on accepted)
  - candidate document uploaded callback
  - hrms handoff callback
- Wait/resume mappings updated for HRMS rejection event handling.

Frontend Status: Partial

Notes:
- `frontend/src/pages/hdc/sections/JoiningTracking.tsx` enhanced with:
  - onboarding status management
  - checklist management UI
  - document status panel
  - handoff preparation trigger
- Frontend build has many pre-existing unrelated TypeScript errors outside Phase 4 scope.

Overall Phase Completion: 90 %

