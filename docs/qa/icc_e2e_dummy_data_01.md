# ICC E2E Dummy Data QA Report

Module ID: `ICC-E2E-DUMMY-DATA-01`

## Seed File / Script

- Management command: `backend/apps/interviews/management/commands/seed_icc_dummy_data.py`
- Run from backend:

```bash
python3 manage.py seed_icc_dummy_data
```

## What Dummy Data Was Created

Tenant scope:

- Demo tenant: `11111111-1111-1111-1111-111111111111`
- Recruiter, HR, hiring manager, scheduler, interviewer, panelist, leadership reviewer, and candidate users

Interview types / registry coverage:

- Existing system registry kept intact
- Required ICC sample coverage ensured for AI, Human, Technical, Assessment, Screening, and Advanced categories

AI interview templates created:

1. `Sales AI Screening`
2. `Customer Support Behavioral AI Screen`
3. `Junior Developer AI Technical Screen`
4. `Finance Analyst Async Text Screen`
5. `Leadership Behavioral One-Way Video`

Each AI template includes:

- setup
- question flow
- candidate experience config
- evaluation dimensions and rubric shell
- scorecard mapping
- outcome / routing logic
- usage shell for linked jobs / flows / stages

Unified reusable interview templates created:

- `Structured Technical Round`
- `HR Final Conversation`
- `Sales Role Play Simulation`
- `Operations Case Study`

Scorecards created:

1. `AI Screening Scorecard`
2. `Technical Scorecard`
3. `HR Scorecard`
4. `Panel Scorecard`
5. `Behavioral Scorecard`
6. `Final Round Scorecard`

Flows created:

1. `Sales Hiring Flow`
2. `Engineering Hiring Flow`
3. `Support Hiring Flow`
4. `Leadership Hiring Flow`

Jobs created:

- `Sales Account Executive`
- `Backend Engineer`
- `Customer Support Specialist`
- `Director of Operations`

Applications created:

- 8 tenant-scoped applications linked to jobs and seeded candidates

Interviews created:

- 10 interviews across `scheduled`, `in_progress`, and `completed`
- candidate runtime shells seeded for:
  - invited
  - started
  - submitted
  - expired
  - blocked
- one candidate self-scheduling link
- one in-progress runtime shell
- four decision records
- panel feedback samples for multi-interviewer review

Question engine data created:

- 6 question bank entries
- 3 question groups
- interview-type and template attachments

Scheduling / integration data created:

- availability profile
- availability blocks
- calendar connection
- provider registry rows if missing
- tenant provider connections
- execution mappings

## Seed Summary

Validated after seeding:

- interview types visible: `64`
- AI templates created: `5`
- scorecards created: `6`
- flows created: `4`
- jobs created: `4`
- applications created: `8`
- interviews created: `10`
- question bank records created: `6`
- question groups created: `3`
- scheduling links created: `1`

Idempotency:

- `python3 manage.py seed_icc_dummy_data` reruns cleanly
- second run did not duplicate seeded records

## End-to-End Scenarios Tested

### Scenario 1 — AI Screening Flow

Seeded candidate:

- `Aisha Khan`

Path:

- candidate application exists
- `Sales AI Screening` template linked
- AI score and overall score stored on interview
- `AI Screening Scorecard` attached
- decision stored as `next_round`
- routing metadata points to `Hiring Manager Interview`

Validation result:

- working

### Scenario 2 — AI Screening Reject

Seeded candidate:

- `Rahul Mehta`

Path:

- candidate completes `Sales AI Screening`
- low AI score stored
- reject recommendation stored
- final decision stored as `reject`

Validation result:

- working

### Scenario 3 — Technical Flow

Seeded candidate:

- `Arjun Rao`

Path:

- `Engineering Hiring Flow` exists
- AI technical stage linked to `Junior Developer AI Technical Screen`
- later technical stages carry scorecard mappings
- scheduled `Technical Interview` exists with panelists and scorecard

Validation result:

- working

### Scenario 4 — Manual Review

Seeded candidate:

- `Priya Nair`

Path:

- completes `Customer Support Behavioral AI Screen`
- borderline result stored
- decision stored as `manual_review`
- outcome metadata routes to manual review queue

Validation result:

- working

### Scenario 5 — Scheduling / Operations

Seeded candidate:

- `Dev Kapoor`

Path:

- scheduled AI interview exists
- scheduling link exists
- availability profile and calendar shell exist
- interview remains visible as upcoming scheduled work

Validation result:

- working

### Scenario 6 — Registry / Template Usage

Path:

- AI templates have linked usage metadata for jobs / flows / stages
- flows embed AI template stage config
- scorecard usage can be derived from template and flow mappings

Validation result:

- working for seeded AI template usage and scorecard linkage

## What Worked

- Backend seed command created realistic ICC data in real DB models
- AI interview templates, scorecards, and flows are linked through actual IDs
- AI evaluation points to scorecard template IDs
- AI flow stages reference reusable AI templates
- operations-facing interview records exist with mixed statuses
- question bank is no longer empty
- scheduling engine has real profile / block / link data
- integration engine has providers, tenant connections, and execution mappings
- candidate runtime and security shells are seeded in interview metadata
- decision engine has real decision rows and history rows

## What Is Partial

- No live browser automation was run in this task; validation is DB / ORM level
- Candidate runtime states are seeded shells and metadata-driven states, not a scripted UI walkthrough
- Flow-to-job usage is represented through flow metadata and AI template usage metadata where current architecture supports it
- Some requested business states like `awaiting_feedback`, `awaiting_decision`, `manual_review`, `rejected`, `shortlisted` are represented through interview decisions, feedback presence, and application status rather than new interview status codes

## What Is Real vs Mock

Real:

- database records for templates, scorecards, flows, jobs, applications, interviews, questions, decisions, scheduling links, availability, provider connections, and mappings

Mock / shell-level:

- external provider auth payloads
- calendar sync details
- AI-generated scoring internals
- candidate runtime protection behavior beyond stored metadata shell
- notification side effects

## Blockers Found

1. Job and candidate reference ID generators can collide in seeded bulk creation when not explicitly provided.
2. Some enterprise usage counts are frontend-derived from metadata or linked JSON rather than a dedicated normalized usage model.
3. Several requested operational states are not first-class interview statuses in the backend model.
4. Candidate runtime and automation are architecturally present but still shell-heavy for true E2E execution.

## Recommended Fixes Before Next Module

1. Add a normalized usage-link model for template-to-job, template-to-flow, and scorecard-to-stage tracking.
2. Introduce richer operational interview states or explicit derived status APIs for queues like awaiting feedback and awaiting decision.
3. Add an official backend seed namespace for reference IDs to avoid manual overrides in future seed scripts.
4. Add smoke API tests for ICC list pages after seeding:
   - `/interviews/templates/`
   - `/interviews/scorecards/templates/`
   - `/interviews/flows/`
   - `/interviews/`
   - `/interviews/questions/bank/`
   - `/interviews/availability/profile/`
   - `/interviews/integrations/providers/`

## Validation Commands Used

```bash
python3 manage.py seed_icc_dummy_data
python3 manage.py shell -c "..."
```
