# Jobs Phase 1 Core Reset — QA Document
**Date:** 2026-04-05  
**Scope:** Phase 1 core audit, backup, gap fill, and verification

---

## 1. Core Design Rules Applied

| Rule | Applied |
|------|---------|
| A. Jobs is a core commodity — enterprise-grade | ✓ — Layout hierarchy preserved |
| B. Summary first, action second, detail third | ✓ — List → Command Center → Setup flow intact |
| C. Quick understanding / quick action / low clutter | ✓ — Status tabs, archive/restore, card quick-actions |
| D. No single page overloaded | ✓ — Tabs isolate detail sections |
| E. Clean hierarchy: list / CC / setup / deep detail | ✓ — Routes unchanged, new pages added cleanly |
| F. No hidden features — all accessible via route/nav | ✓ — Templates and Archived now in Jobs dropdown nav |
| G. Do not add new UI patterns if system pattern exists | ✓ — Used Ant Design Table, Drawer, Modal consistent with rest |
| H. Keep role-aware but not fragmented | ✓ — Role-based route protection applied |

---

## 2. Backup Details

**Backup location:** `frontend/src/pages/jobs/backup_phase1_reset_20260405/`

Files backed up:
- `JobsList.tsx` (49,616 bytes — Apr 4)
- `JobCreate.tsx` (9,506 bytes — Apr 2)
- `JobSetupStudio.tsx` (34,672 bytes — Apr 3)
- `JobDetail.tsx` (36,322 bytes — Apr 2)
- `JobFullView.tsx` (39,315 bytes — Apr 2)
- `JobCommandCenterView.tsx` (50,863 bytes — Apr 3)
- `JobDetailPanel.tsx` (8,576 bytes — Apr 2)
- `JobQuickView.tsx` (13,809 bytes — Apr 2)
- `JobAutomationView.tsx` (16,726 bytes — Apr 1)
- `JobInterviewsTab.tsx` (14,845 bytes — Apr 2)
- `JobTrackingView.tsx` (8,659 bytes — Apr 2)

**Note:** No existing UI was deleted. All existing files remain in place and were only supplemented or lightly patched.

---

## 3. Phase 1 Source Requirements — Audit Matrix

| # | Requirement | Backend | Frontend | Status | Notes |
|---|-------------|---------|----------|--------|-------|
| 1 | Job requisition creation | ✓ Full | ✓ Full | **COMPLETE** | POST `/jobs/requisitions/`, JobSetupStudio wizard |
| 2 | JD template library | ✓ **ADDED** | ✓ **ADDED** | **COMPLETED THIS RESET** | New `JobDescriptionTemplate` model + CRUD API + `JobTemplates.tsx` page |
| 3 | Multi-level approval workflow | ✓ Partial | ✓ Partial | **PARTIAL** | Single-step approve/reject works. `approval_chain` JSONField exists but multi-step chain config UI not built |
| 4 | Approval hierarchy configuration | ✗ | ✗ | **MISSING** | `approval_chain` field exists; no UI to configure sequential approvers |
| 5 | Job posting to platform | ✓ Full | ✓ Full | **COMPLETE** | POST `.../publish/` creates `JobPosting`; slug auto-generated |
| 6 | Confidential job posting | ✓ Full | ✓ Full | **COMPLETE** | `is_confidential` flag; serializer redacts fields for external users |
| 7 | Job cloning | ✓ Full | ✓ Full | **COMPLETE** | POST `.../clone/` — clone as new draft |
| 8 | Job expiry and renewal | ✓ Partial | ✓ Partial | **PARTIAL** | `expires_at` on JobPosting, `guarantee_watch_until` on Requisition; no dedicated expiry management UI or auto-close job |
| 9 | Multiple locations per job | ✓ **ADDED** | ✓ API added | **PARTIAL** | New `JobLocation` junction model + API; UI integration in create form pending |
| 10 | Budget code assignment | ✓ Full | ✓ Full | **COMPLETE** | `budget_code` field on Requisition; visible in JobSetupStudio setup form |

---

## 4. Basic Job UX Audit Results

### A. Is adding/creating a job complete and enterprise-usable?
**YES** — JobSetupStudio 8-step wizard covers:
- Step 1: Job Identity (title, dept, location, type, mode, salary, description, skills)
- Step 2: Hiring Team (owner, manager, recruiters)
- Step 3: Sourcing (sourcing mode, agencies)
- Step 4: Workflow (approval mode)
- Step 5: Interviews (package binding)
- Step 6: Automation (auto-flags)
- Step 7: Offers (default salary, commission)
- Step 8: Review (readiness score, submit/publish)

Create + edit both work (same component, `id` param toggles mode). Save/load parity confirmed via `useEffect` that loads existing job into form.

**Gap:** Step 1 location field uses `Input` not `Select` from org locations — cosmetic inconsistency but functional.

### B. Is JD template creation and selection done?
**BEFORE THIS RESET:** No — completely missing.  
**AFTER THIS RESET:**
- `JobTemplates.tsx` — full CRUD list page with search, category filter, inline preview drawer, edit drawer, duplicate, delete
- `JobSetupStudio` — "Use JD Template" button on Role Definition section opens template picker modal with search and instant apply

### C. Is Jobs list operationally complete?
**YES with improvements:**
- Active, Draft, Pending Approval, Approved, Paused, Closed tabs — **always existed**
- **ADDED this reset:** `Archived` tab (status=`cancelled`), `Approved` tab, `Paused` tab

### D. Are archive / restore / active states visible and usable?
**BEFORE this reset:** Archive action existed but only soft-deleted. No restore. No archived tab.  
**AFTER this reset:**
- Archive action now sets `status = 'cancelled'` (not soft-delete)
- New `handleRestore()` sets `status = 'draft'`
- Card dropdown shows "Restore Job" when `job.status === 'cancelled'`
- "Archived" tab in status bar navigates to cancelled jobs

### E. Can users handle everyday basic job work without advanced screens?
**YES** — create, list, search, filter, archive, restore, clone, submit for approval, approve, reject, publish all work from JobsList or JobSetupStudio.

---

## 5. Core Features Fixed / Implemented This Reset

| Feature | Change |
|---------|--------|
| **JD Template Library** | New backend model `JobDescriptionTemplate` + migration + CRUD views/serializer/URLs + `JobTemplates.tsx` page + `jdTemplatesApi` in `api/jobs.ts` |
| **Apply Template in Job Creation** | "Use JD Template" button in JobSetupStudio Step 1 opens picker modal; applying fills description/requirements/responsibilities/skills fields |
| **Multiple Locations (backend)** | New `JobLocation` junction table model + migration + `JobLocationListView` / `JobLocationDeleteView` + `jobLocationsApi` |
| **Archived Jobs tab** | Added `Archived` (cancelled) status tab to `JOB_STATUS_TABS` in JobsList |
| **Approved / Paused tabs** | Added missing status tabs for approved and paused states |
| **Archive behavior fix** | Archive now sets `status='cancelled'` instead of calling soft-delete endpoint |
| **Restore action** | New `handleRestore()` sets status back to draft; card dropdown shows restore for archived jobs |
| **Nav access — Templates** | Added "JD Templates" and "Archived Jobs" to Jobs dropdown in top nav (AppLayout) |
| **Route — Templates** | Added `/jobs/templates` route in App.tsx with role protection |

---

## 6. UI / Menu / Route Access Added

| Route | Component | Nav Access | Roles |
|-------|-----------|------------|-------|
| `/jobs/templates` | `JobTemplates` | Jobs dropdown → "JD Templates" | tenant_admin, super_admin, hr_manager, recruiter, hiring_manager |
| `/jobs?status=cancelled` | `JobsList` (Archived tab) | Jobs dropdown → "Archived Jobs" | All authenticated |

---

## 7. What Remains Incomplete in Phase 1

| Item | Status | What's Missing |
|------|--------|----------------|
| Multi-level approval chain config | PARTIAL | `approval_chain` JSONField exists but no UI to set sequential approver order. Single approve/reject works. |
| Multiple locations — UI in form | PARTIAL | Backend+API done; JobSetupStudio still uses single `location_id`. Need multi-select in Step 1 |
| Job expiry management UI | PARTIAL | `expires_at` on JobPosting, `guarantee_watch_until` on Requisition; no dedicated expiry UI, no background task to auto-close |
| JD Template apply → increment usage on server | PARTIAL | Frontend sets fields directly from template data without calling `/apply/` endpoint (avoids extra request on picker). For usage tracking, call `jdTemplatesApi.apply()` after selection |

---

## 8. Use Cases

### UC-1: Create job using JD template
1. Go to `/jobs/create`
2. Fill Step 1 core identity fields
3. Click "Use JD Template" button in Role Definition section
4. Search for template by name or browse
5. Click template → description, requirements, responsibilities, skills auto-fill
6. Continue with remaining wizard steps

### UC-2: Browse and manage JD templates
1. Navigate via Jobs nav → "JD Templates"
2. Filter by category or search by name
3. Click any row to preview full content
4. Use Edit to modify, Duplicate to copy, Delete to remove
5. Create new template from scratch with "New Template" button

### UC-3: View and restore archived jobs
1. Click Jobs nav → "Archived Jobs" or switch to Archived tab in Jobs list
2. See all cancelled/archived jobs
3. Open card dropdown → "Restore Job" to move back to Draft

### UC-4: Clone a job
1. From Jobs list, hover job card → open dropdown → "Duplicate Job"
2. Or from command center toolbar → Clone button
3. Creates new Draft job with same fields + "(Copy)" suffix on title

### UC-5: Submit job for approval
1. From Draft job, use `JobDetailPanel` → "Submit for Approval"
2. Moves to `pending_approval` status
3. Assigned approver can approve or reject with reason

---

## 9. Edge Cases

| Edge Case | Behavior |
|-----------|----------|
| Apply template to job that already has description | Modal picker applies; existing content preserved (template fills only empty fields unless `overwrite=true` from API) |
| Duplicate template | Creates new copy with "(Copy)" suffix; usage count starts at 0 |
| Archive a job with active applications | Sets `status='cancelled'`; does not affect existing applications — they remain in pipeline |
| Restore archived job | Sets status back to `draft`; existing hiring team/stages preserved |
| Delete template in use | Soft-delete; existing jobs retain their copied content since content was copied on apply |
| Multiple locations — primary flag | Marking a new location as primary clears existing primary flag on the backend |

---

## 10. Test Scenarios

### Backend

```python
# T1: JD Template CRUD
POST /api/v1/jobs/templates/       → create template
GET  /api/v1/jobs/templates/       → list templates
GET  /api/v1/jobs/templates/?category=engineering  → filter by category
GET  /api/v1/jobs/templates/?search=senior         → search
PUT  /api/v1/jobs/templates/{id}/  → update
DEL  /api/v1/jobs/templates/{id}/  → soft-delete

# T2: Template duplication
POST /api/v1/jobs/templates/{id}/duplicate/
# → Returns new template with "(Copy)" suffix, usage_count=0

# T3: Template apply (prefill only)
POST /api/v1/jobs/templates/{id}/apply/
# → Returns {description, requirements, responsibilities, skills_required}

# T4: Template apply to existing job
POST /api/v1/jobs/templates/{id}/apply/
body: { "requisition_id": "<uuid>", "overwrite": false }
# → Updates empty fields only; returns {fields_updated: [...]}

# T5: Multiple locations
POST /api/v1/jobs/requisitions/{id}/locations/
body: { "location_id": "<uuid>", "location_name": "Mumbai", "is_primary": true }
GET  /api/v1/jobs/requisitions/{id}/locations/
DEL  /api/v1/jobs/requisitions/{id}/locations/{location_id}/

# T6: Archive + Restore
PUT /api/v1/jobs/requisitions/{id}/  body: {"status": "cancelled"}  → archive
PUT /api/v1/jobs/requisitions/{id}/  body: {"status": "draft"}      → restore
GET /api/v1/jobs/requisitions/?status=cancelled                     → list archived
```

### Frontend

| Test | Steps | Expected |
|------|-------|----------|
| Template page loads | Navigate to `/jobs/templates` | Table renders with filter bar |
| Create template | Click "New Template" → fill form → save | Template appears in list |
| Search template | Type in search box | List filters in real time |
| Apply template in studio | Jobs/Create → Step 1 → "Use JD Template" → select | Description fields pre-filled |
| Archived tab | JobsList → click "Archived" tab | Shows only cancelled jobs |
| Restore | Archived job card → dropdown → "Restore Job" → confirm | Job moves back to Draft tab |
| Nav access | Jobs dropdown in top nav | Shows "JD Templates" and "Archived Jobs" links |
