# Test Cases — Automation Command Center

Module: Intelligence Hub → Automation Command Center
Page: `/automation-center`

---

## TC-ACC-001 — Active Workflows Shown in Overview

**Precondition:** Two active workflows exist for the tenant.

**Steps:**
1. Authenticate as tenant_admin.
2. GET `/api/v1/automation-center/overview/`

**Expected:**
- `active_workflows` ≥ 2 in response.
- HTTP 200.

---

## TC-ACC-002 — Executions Today and Success Rate Computed Correctly

**Precondition:** 8 completed + 2 failed executions today for a workflow.

**Steps:**
1. GET `/api/v1/automation-center/overview/`

**Expected:**
- `executions_today` = 10
- `success_rate` = 80.0
- `failures_today` = 2

---

## TC-ACC-003 — Failing Workflow Shown in Health

**Precondition:** A workflow has at least one failed execution today.

**Steps:**
1. GET `/api/v1/automation-center/health/`

**Expected:**
- `failing_workflows` ≥ 1.
- HTTP 200.

---

## TC-ACC-004 — Paused Workflow Shown in Health

**Precondition:** A workflow has status=paused.

**Steps:**
1. GET `/api/v1/automation-center/health/`

**Expected:**
- `paused_workflows` ≥ 1.

---

## TC-ACC-005 — AI Suggestion Visible in Suggestions Feed

**Precondition:** An AISuggestion exists with status=pending for the tenant.

**Steps:**
1. GET `/api/v1/automation-center/ai-suggestions/`

**Expected:**
- Response array contains the suggestion.
- `title` matches created suggestion.
- HTTP 200.

---

## TC-ACC-006 — Pause All Automation

**Precondition:** 3 active workflows exist. Authenticated as tenant_admin.

**Steps:**
1. POST `/api/v1/automation-center/pause-all/`

**Expected:**
- HTTP 200.
- `paused_count` = 3.
- All 3 workflows now have status=paused in DB.

---

## TC-ACC-007 — Resume All Automation

**Precondition:** 3 paused workflows exist. Authenticated as tenant_admin.

**Steps:**
1. POST `/api/v1/automation-center/resume-all/`

**Expected:**
- HTTP 200.
- `resumed_count` = 3.
- All workflows now have status=active.

---

## TC-ACC-008 — Recruiter Cannot Pause All (Permission Denied)

**Precondition:** Authenticated as recruiter.

**Steps:**
1. POST `/api/v1/automation-center/pause-all/`

**Expected:**
- HTTP 403.

---

## TC-ACC-009 — Recruiter Cannot Emergency Stop

**Precondition:** Authenticated as recruiter.

**Steps:**
1. POST `/api/v1/automation-center/emergency-stop/`

**Expected:**
- HTTP 403.

---

## TC-ACC-010 — Emergency Stop Deactivates All Workflows and Stops Running Executions

**Precondition:** 1 active workflow with 1 running execution. Authenticated as tenant_admin.

**Steps:**
1. POST `/api/v1/automation-center/emergency-stop/`

**Expected:**
- HTTP 200.
- `deactivated_workflows` ≥ 1.
- `stopped_executions` ≥ 1.
- Workflow status = archived, is_active = false.
- Execution status = failed.

---

## TC-ACC-011 — Workflow List Search Filter

**Precondition:** Two workflows: "Offer Reminder Flow" and "Interview Reminder Flow".

**Steps:**
1. GET `/api/v1/automation-center/workflows/?search=Offer`

**Expected:**
- Only "Offer Reminder Flow" returned.
- HTTP 200.

---

## TC-ACC-012 — Activity Feed Returns Recent Events

**Precondition:** One completed execution exists.

**Steps:**
1. GET `/api/v1/automation-center/activity/`

**Expected:**
- Response array has ≥ 1 item.
- Each item contains `time`, `workflow_name`, `action`, `entity_type`, `status`.

---

## TC-ACC-013 — UI Section Navigation

**Steps:**
1. Navigate to `/automation-center`.
2. Click "Active Workflows" tab.

**Expected:**
- URL changes to `/automation-center/workflows`.
- Workflow table renders.

---

## TC-ACC-014 — Global Controls Button Visible to Admin Only

**Steps (Admin):**
1. Login as tenant_admin.
2. Navigate to `/automation-center`.

**Expected:**
- "Global Controls" button visible.

**Steps (Recruiter):**
1. Login as recruiter.
2. Navigate to `/automation-center`.

**Expected:**
- "Global Controls" button NOT visible.

---

## TC-ACC-015 — Multi-Tenant Isolation

**Precondition:** Two tenants (A and B) each with their own workflows.

**Steps:**
1. Authenticate as Tenant A admin.
2. GET `/api/v1/automation-center/workflows/`

**Expected:**
- Only Tenant A's workflows returned.
- Tenant B's data not visible.
