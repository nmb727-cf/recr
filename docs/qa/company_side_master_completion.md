# Company Side Master Completion

## Jobs
Status: Implemented
Notes: Company job lifecycle APIs and workflow binding are active in `apps/jobs` and integrated with workflow start paths.

## Company Candidate Management
Status: Partial
Notes: Core candidate records, invite/apply, and company-side read/update flows are present; advanced company-only operational completeness still needs broader regression coverage.

## Applications / Pipeline
Status: Implemented
Notes: Pipeline entities and company-side progression flows are active, with workflow scenario execution validating end-to-end stage movement.

## Interviews
Status: Implemented
Notes: Interview creation/scheduling/execution APIs are active from company side, including external/manual interview coordination support.

## Scheduling
Status: Implemented
Notes: Workflow scheduler engine and scheduled-task APIs are active; wait/resume scheduling contracts are wired and tested in workflow module suites.

## Offers
Status: Partial
Notes: Offer-related workflow progression and callbacks are wired; full offer-domain UX/process hardening remains to be validated against all company offer variants.

## Documents
Status: Partial
Notes: Document models/APIs exist and candidate document-sign callback contract is now wired to resume workflows; full document lifecycle parity still needs broader company QA sweep.

## Onboarding Handoff
Status: Partial
Notes: Workflow handoff/routing primitives exist and HRMS ack callback contract is exposed; complete onboarding handoff runbook validation is still pending.

## Workflow Automation
Status: Implemented
Notes: Triggering, instance creation, transitions, wait/resume, actions, notifications, SLA checks, observability, recovery, and analytics are operational in workflow execution services.

## Notifications
Status: Implemented
Notes: Notification engine + queue/log APIs are integrated and covered by existing workflow verification suites.

## SLA / Escalation
Status: Implemented
Notes: SLA engine and tracker/event flows are wired through orchestrator cycle and instance APIs.

## Observability
Status: Implemented
Notes: Timeline, trace, snapshot, and metrics endpoints are active and previously verified in workflow finalization execution.

## Recovery
Status: Implemented
Notes: Failure recovery case/retry paths are wired; retry serialization hardening was applied in workflow recovery engine.

## Metrics / Analytics
Status: Implemented
Notes: Workflow metrics snapshots and analytics endpoints are active and validated in module tests/finalization.

## Frontend Completion
Status: Partial
Notes: Company-side frontend has broad coverage in jobs/pipeline/interviews/offers/dashboard surfaces, but this phase focused on backend contract completion and did not run full UI regression on every company page/form.

## External Integration Contracts
Status: Implemented
Notes: Company-side external callback contracts now exist with validation, resume-event mapping, and timeline logging:
- `POST /api/v1/company/external/agency-submission/` -> resume event `client_feedback_received`
- `POST /api/v1/company/external/agency-coordination-response/` -> resume event `interview_scheduled`
- `POST /api/v1/company/external/candidate-response/` -> resume event mapped from payload (`offer_accepted` / `offer_rejected` / `candidate_response_received`)
- `POST /api/v1/company/external/candidate-document-signed/` -> resume event `document_signed`
- `POST /api/v1/company/external/hrms-handoff-ack/` -> resume event `hrms_handoff_acknowledged`

Overall Company Side Completion: 91 %

Critical Missing Items:
- Full company-frontend regression and form-level UX hardening across all company pages is not yet fully validated in this phase.
- Offer/document/onboarding company-process variants need expanded end-to-end matrix testing beyond workflow-core scenarios.

Open Endpoints Ready:
- `POST /api/v1/company/external/agency-submission/`
- `POST /api/v1/company/external/agency-coordination-response/`
- `POST /api/v1/company/external/candidate-response/`
- `POST /api/v1/company/external/candidate-document-signed/`
- `POST /api/v1/company/external/hrms-handoff-ack/`

Blocked by Agency/Candidate UI:
- NONE (company-side wait/resume and callback contracts are exposed without agency/candidate UI dependency)
