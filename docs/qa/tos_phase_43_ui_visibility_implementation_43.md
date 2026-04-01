# TOS-UI-VISIBILITY-IMPLEMENTATION-43

## 1. Scope

Purpose:
- expose already-built ATS, ICC, HDC, and supporting modules through visible navigation
- connect menu entries to stable routes
- replace hidden or dead-end entries with usable routed destinations
- seed demo data so major screens do not render as empty shells

This phase focused on visibility, routing continuity, seeded examples, and inspectable UI, not new architecture design.

## 2. Navigation And Routing

Major navigation exposure added or expanded for:
- ATS core
- ICC
- HDC
- activity log
- notifications
- workflow templates
- candidate interview experience routes

Key route outcomes:
- HDC now has a dedicated routed workspace under `/hiring-decisions` and `/hiring-decisions/:section`
- approvals now resolve to `/hiring-decisions/approvals`
- offers now resolve to `/hiring-decisions/offer-release`
- candidate database, leads, active work, and pools now resolve to explicit ATS pages
- ICC registry, templates, scorecards, scheduling, recruiter views, queue, productivity, and multiple engine entry points are wired to real pages
- activity log, notifications, and workflow templates now render seeded shell pages instead of generic coming-soon views

## 3. Demo Data And Templates

Frontend-seeded demo visibility data added for:
- HDC overview
- committee
- comparison
- approvals
- offer intelligence
- compensation
- negotiation
- offer release
- offer acceptance
- joining
- workflow templates
- notifications
- activity log

Backend demo data seeded:
- `python3 backend/manage.py seed_icc_dummy_data`
- `python3 backend/manage.py seed_email_template_bodies`

ICC seed results available for live UI inspection include:
- interview templates
- scorecards
- interview types
- interviews
- jobs
- applications
- question bank content

## 4. Placeholder Policy

Where full operational UI was not yet implemented, stable visibility shells were added with:
- page title
- module context
- summary cards
- seeded example records
- explicit visibility callout

This applies mainly to HDC operational areas and selected support pages.

## 5. Verification Status

Completed:
- menu entries added or corrected
- routes added or corrected
- HDC visibility shells added
- support shells for workflow templates, notifications, and activity log added
- demo data added for major HDC and support sections
- admin/test visibility widened for routed HDC access

Build note:
- the frontend build remains blocked by multiple pre-existing TypeScript issues in older ATS/ICC pages unrelated to this visibility pass
- visibility-shell typing regressions introduced in this phase were corrected

## 6. Inspect Paths

Primary inspect paths:
- `/jobs`
- `/pipeline`
- `/candidates`
- `/candidates/active`
- `/candidates/leads`
- `/candidates/pools`
- `/applications`
- `/interviews`
- `/interviews/registry`
- `/interviews/templates`
- `/interviews/scorecards`
- `/interviews/scheduling`
- `/interviews/dashboard`
- `/interviews/queue`
- `/interviews/productivity`
- `/interviews/live`
- `/interviews/automation`
- `/interviews/integrations`
- `/interviews/ai`
- `/interviews/technical`
- `/interviews/human`
- `/interviews/video`
- `/interviews/group-discussion`
- `/interviews/presentation-interview`
- `/interviews/portfolio-review`
- `/interviews/prequalification`
- `/hiring-decisions`
- `/hiring-decisions/committee`
- `/hiring-decisions/comparison`
- `/hiring-decisions/approvals`
- `/hiring-decisions/offer-intelligence`
- `/hiring-decisions/compensation`
- `/hiring-decisions/negotiation`
- `/hiring-decisions/offer-release`
- `/hiring-decisions/offer-acceptance`
- `/hiring-decisions/joining`
- `/activity-log`
- `/notifications`
- `/workflow-templates`

## 7. Files Touched

Frontend:
- `frontend/src/App.tsx`
- `frontend/src/config/navigation.tsx`
- `frontend/src/components/demo/VisibilityShellPage.tsx`
- `frontend/src/data/uiVisibilityDemo.ts`
- `frontend/src/pages/hdc/HiringDecisionWorkspace.tsx`
- `frontend/src/pages/system/WorkflowTemplatesPage.tsx`
- `frontend/src/pages/system/NotificationsCenterPage.tsx`
- `frontend/src/pages/system/ActivityLogPage.tsx`
- `frontend/src/pages/dashboard/HiringCommandCenter.tsx`

Data seeding:
- `backend/apps/interviews/management/commands/seed_icc_dummy_data.py`
- `backend/apps/communications/management/commands/seed_email_template_bodies.py`
