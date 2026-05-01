# Jobs Phase 1 Completion — QA Document
**Date:** 2026-04-05  
**Scope:** Step-by-step completion of all Phase 1 core job form, location, approval, and expiry features.

---

## 1. Job Form Audit Result

### Step 1 — Job Identity & Parameters

| Field | Before | After | Notes |
|-------|--------|-------|-------|
| Job Title | ✓ | ✓ | `title` field, required |
| Department | ✓ | ✓ | `department_id` Select |
| Location | ✗ broken | ✓ Fixed | Was `Input` mapped to wrong field `location`. Now `LocationMultiSelect` with `location_id` per org locations. |
| Multiple Locations | ✗ | ✓ Added | `LocationMultiSelect` component with primary flag |
| Employment Type | ✓ | ✓ | `job_type` |
| Work Mode | ✓ | ✓ | `work_mode` |
| Priority | ✓ | ✓ | `priority` |
| Headcount | ✓ | ✓ | `headcount` |
| Target Hire Date | ✓ | ✓ | `target_date` |
| **Posting Expiry Date** | ✗ | ✓ Added | `expiry_date` stored in `metadata.expiry_date` |
| Budget Code | ✓ | ✓ | `budget_code` |
| Confidential Toggle | ✓ | ✓ | `is_confidential` checkbox |
| Experience Min/Max | ✓ | ✓ | `experience_min` / `experience_max` |
| Salary Range | ✓ | ✓ | `salary_min` / `salary_max` / `salary_currency` / `salary_visible` |
| Description | ✓ | ✓ | `description` textarea |
| Responsibilities | ✓ | ✓ | `responsibilities` textarea |
| Requirements | ✓ | ✓ | `requirements` textarea |
| Skills | ✓ | ✓ | `skills_required` tag select |
| JD Template Apply | ✓ | ✓ | "Use JD Template" button + picker modal |

### Step 2 — Hiring Team

| Field | Before | After |
|-------|--------|-------|
| Job Owner | ✓ | ✓ |
| Hiring Manager | ✓ | ✓ |
| Primary Recruiters | ✓ | ✓ |
| **Backup Recruiter** | ✗ | ✓ Added |
| **Coordinator** | ✗ | ✓ Added |

### Step 3 — Sourcing

| Field | Before | After | Notes |
|-------|--------|-------|-------|
| Sourcing Mode | ✓ partial | ✓ Fixed | Was mapped to `metadata.sourcing_mode`. Now maps to real model field `sourcing_mode` with correct values (`internal_only`, `hybrid`, `external_only`) |
| Agency Assignment | ✓ | ✓ | |
| Auto-distribute | ✓ | ✓ | |

### Step 4 — Workflow (was just static UI)

| Feature | Before | After |
|---------|--------|-------|
| Pipeline stages display | Static | ✓ Horizontal flow display |
| **Approval Required toggle** | ✗ | ✓ Added |
| **Approval chain builder** | ✗ | ✓ Added (`ApprovalChainBuilder` component) |
| Add/remove approvers | ✗ | ✓ |
| Reorder approvers (up/down) | ✗ | ✓ |
| Fallback approver toggle | ✗ | ✓ |
| Approval flow preview | ✗ | ✓ Visual flow diagram |

---

## 2. Fields Added This Session

| Field | Location | Stored As |
|-------|----------|-----------|
| `expiry_date` | Step 1 — Posting Expiry | `metadata.expiry_date` (ISO date string) |
| `backup_recruiter_id` | Step 2 — Backup Recruiter | `backup_recruiter_id` on JobRequisition model |
| `coordinator_id` | Step 2 — Coordinator | `coordinator_id` on JobRequisition model |
| `approval_chain` | Step 4 — Approval builder | `approval_chain` JSONField on JobRequisition |
| Multiple `location_ids` | Step 1 — Location multi-select | `JobLocation` junction table via API |

---

## 3. UI Implemented

### `ApprovalChainBuilder` component (in JobSetupStudio.tsx)
- Controlled list of `ApproverEntry` objects
- Each entry: user select (searchable), fallback toggle, remove button, up/down reorder
- Empty state: "No approval required" info panel
- When filled: live flow diagram shows Submit → Approver 1 → Approver 2 → Active
- Fallback approvers shown with `UserCheck` icon and "FALLBACK" label
- Warning banner explains sequential approval behavior

### `LocationMultiSelect` component (in JobSetupStudio.tsx)
- Controlled list of `LocationEntry` objects
- Each entry: location name, primary badge/button, remove button
- Add via Select dropdown (filters out already-added locations)
- First added = auto-set as primary
- "Set Primary" button on non-primary entries
- Synced with `JobLocation` API on save (via `jobLocationsApi.add()`)

### Expiry badge in `JobOperationalCard` (JobsList.tsx)
- `isExpired`: red "Expired" badge when expiry date is in the past
- `isExpiringSoon`: amber "Expiring in X days" badge when ≤7 days remaining
- Confidential jobs show "Conf." grey badge
- All badges appear inline with status pill

---

## 4. Approval UI Status

**COMPLETE for Phase 1:**
- Toggle on/off approval requirement
- Add sequential approvers (from user list)
- Remove approvers
- Reorder approvers (up/down buttons)
- Set fallback approver per entry
- Visual flow diagram showing approval path
- Data stored in `approval_chain` JSONField on save
- On submit-for-approval: existing backend `JobRequisitionSubmitView` uses `status = 'pending_approval'` — the chain is now populated

**What approval_chain JSON looks like when saved:**
```json
[
  {"user_id": "uuid-1", "name": "John Doe", "order": 1, "is_fallback": false},
  {"user_id": "uuid-2", "name": "Jane Smith", "order": 2, "is_fallback": true}
]
```

**Fixed this session:**
- Submit endpoint now sets `current_approver_id = chain[0].user_id`
- Publish endpoint now blocks if `approval_chain` is non-empty and status is `draft`
- Clone endpoint now resets `approval_chain = []` and `current_approver_id = None`
- JobDetailPanel shows "Awaiting approval from: {name}" alert when pending_approval

**Note:** The backend `approve` endpoint is single-step. Multi-hop sequential approval (checking chain order, advancing to next approver) is a Phase 2 enhancement.

---

## 5. Multiple Location UI Status

**COMPLETE for Phase 1:**
- Multi-select location component in Step 1
- Add/remove locations
- Set/change primary location
- Data saved via `JobLocation` API after requisition save
- Primary location also synced to `location_id` on requisition (for backward compatibility)
- Edit mode: existing locations loaded from `GET /jobs/requisitions/{id}/locations/`

**API behavior:**
- `POST /jobs/requisitions/{id}/locations/` — adds location
- If `is_primary=true`, backend clears previous primary flag
- `DELETE /jobs/requisitions/{id}/locations/{location_id}/` — removes

---

## 6. Expiry UI Status

**COMPLETE for Phase 1:**
- "Posting Expiry" DatePicker in Step 1
- Past dates disabled
- Stored in `metadata.expiry_date`
- Expiry badges visible on job cards in JobsList:
  - Red "Expired" badge when past expiry
  - Amber "Expiring in X days" badge when ≤7 days remaining
- Review step shows expiry date in launch summary

**Phase 2 enhancement needed:**
- Background task (Celery) to auto-close expired jobs
- Notification/alert when job expires

---

## 7. Template Verification

| Scenario | Status |
|----------|--------|
| Template search in picker modal | ✓ Works — debounced search via query key |
| Template preview in JobTemplates page | ✓ Works — `TemplatePreviewDrawer` |
| Apply template fills description, requirements, responsibilities, skills | ✓ Works |
| Template only fills empty fields (non-destructive) | ✓ `tpl.description || form.getFieldValue('description')` |
| Template picker shows "no templates" with link to library | ✓ Works |
| `jdTemplates` extraction fixed for different API shapes | ✓ Fixed — checks both `data?.templates` and `data?.data?.templates` |

---

## 8. Use Cases

### UC-1: Create job with multiple locations
1. New Job → Step 1
2. In "Job Locations" section, use Select to add first location → auto-set as Primary
3. Add second location → "Set Primary" button available
4. On save: `JobLocation` records created for each selected location

### UC-2: Create job requiring approval
1. New Job → Step 4 (Workflow)
2. Toggle "Approval Required" ON
3. Click "+ Add Approver" → select user from dropdown
4. Add fallback approver if needed
5. Flow diagram shows the approval path
6. On save: `approval_chain` JSONField populated
7. Submit for approval → job moves to `pending_approval`

### UC-3: Set job expiry
1. New Job → Step 1
2. Set "Posting Expiry" date
3. Save → `metadata.expiry_date` stored
4. In Jobs list → expiry badge appears on card:
   - Orange "Expiring in 3 days" if within 7 days
   - Red "Expired" if past

### UC-4: Edit job — backup recruiter and coordinator
1. Open existing job → Setup Studio
2. Step 2 → Assign backup recruiter and coordinator
3. Save → `backup_recruiter_id` and `coordinator_id` persisted on model

---

## 9. Edge Cases

| Case | Behavior |
|------|----------|
| Approval chain with empty user_id | Filtered out of preview; validation should catch before submit |
| Remove last location | List empties; form shows "Add at least one location" warning |
| Change primary location | New primary set; old primary cleared |
| Apply template overwrites existing content | Non-destructive: only fills empty fields. Existing content preserved |
| `expiry_date` before `target_date` | No validation — user can set any future date |
| Reorder approver to top | `moveUp` disabled for index 0 |
| Save fails partway through (e.g. locations API error) | Location sync error is caught and non-fatal; job is saved |

---

## 10. Test Scenarios

### Form field validation
```
T1: Submit Step 1 without title → "required" validation shows
T2: Submit Step 1 without department → "required" validation shows
T3: Step 4: Toggle approval ON → add user → flow preview shows
T4: Step 4: Toggle approval OFF → chain clears → "no approval required" state
T5: Step 2: Set backup recruiter + coordinator → on save check API payload includes both
```

### Multiple locations
```
T6: Add 2 locations in step 1 → save → GET /jobs/{id}/locations/ returns 2 records
T7: Add location 1 as primary → add location 2 → location 1 still primary
T8: Set location 2 as primary → location 1 loses primary flag
T9: Remove location → removed from list immediately
```

### Expiry badges
```
T10: Set expiry_date = yesterday → card shows red "Expired" badge
T11: Set expiry_date = 3 days from now → card shows amber "Expiring in 3 days" badge
T12: No expiry_date → no expiry badge shown
```

### Approval chain
```
T13: Create job with approval_chain = [{user_id, name, order: 1, is_fallback: false}] → saved correctly
T14: Submit for approval → status changes to pending_approval, current_approver_id = chain[0].user_id
T15: Approve → status changes to approved
T16: Reject with reason → status reverts to draft, closed_reason set
T17: Publish draft with approval_chain set → blocked with "submit for approval first" error
T18: Clone job → cloned job has empty approval_chain and null current_approver_id
T19: pending_approval job → detail panel shows "Awaiting approval from: <name>" alert
```

---

## 11. Behavior Audit — Phase 1 Verification Matrix

**Audit Date:** 2026-04-05

| Feature | Classification | Backend Behavior | Frontend Behavior | Notes |
|---------|---------------|-----------------|-------------------|-------|
| Job create (wizard) | **COMPLETE** | POST /jobs/requisitions/ works | 8-step wizard, all fields saved | |
| Job edit (same wizard) | **COMPLETE** | PUT with partial update | `id` param loads existing job | |
| JD Template library | **COMPLETE** | CRUD + duplicate + apply views | JobTemplates.tsx page | apply increments usage_count |
| Apply template to job | **COMPLETE** | `/apply/` endpoint available | Non-destructive: fills empty fields only | |
| Multiple locations | **COMPLETE** | JobLocation junction model + API | LocationMultiSelect component | Edit mode diffs/syncs correctly (fixed) |
| Approval chain — store | **COMPLETE** | approval_chain JSONField on model | ApprovalChainBuilder saves chain | |
| Approval chain — submit | **COMPLETE** | Sets current_approver_id = chain[0] | Submit button from draft panel | Fixed this session |
| Approval chain — enforce on publish | **COMPLETE** | Blocks publish-from-draft if chain set | Publish only shown when status=approved | Fixed this session |
| Approval chain — sequential enforce | **MISSING (Phase 2)** | Approve endpoint is single-step | — | Multi-hop chain not enforced; tracked for Phase 2 |
| Approval pending — visibility | **COMPLETE** | current_approver_id stored | Alert shows current approver name | Added this session |
| Clone job | **COMPLETE** | Resets status/approval/chain | Clone button always visible | Fixed: chain cleared on clone |
| Archive job | **COMPLETE** | status='cancelled' | Archive dropdown action | |
| Restore archived job | **COMPLETE** | status='draft' | Restore shown for cancelled cards | |
| Expiry date — store | **COMPLETE** | metadata.expiry_date (ISO string) | DatePicker in Step 1 | |
| Expiry badge — card | **COMPLETE** | — | Red/amber badges in JobOperationalCard | |
| Expiry auto-close | **MISSING (Phase 2)** | No Celery task | — | Needs background worker |
| Confidential flag | **COMPLETE** | is_confidential field; serializer redacts | Checkbox in Step 1, "Conf." badge on card | |
| Publish to posting | **COMPLETE** | Creates JobPosting, slug auto-generated | Publish button for approved jobs | |
| Backup recruiter / coordinator | **COMPLETE** | Model fields exist | Step 2 selects added | |
| Sourcing mode values | **COMPLETE** | internal_only / hybrid / external_only | Fixed radio values in Step 3 | |
| Archive tab in list | **COMPLETE** | status=cancelled filter | Archived tab in JobsList | |
| Nav access — templates | **COMPLETE** | — | Jobs dropdown → JD Templates | |
| Nav access — archived | **COMPLETE** | — | Jobs dropdown → Archived Jobs | |

### Known Phase 2 Items (Intentionally Deferred)
- Multi-hop sequential approval enforcement (chain order check in ApproveView)
- Celery task to auto-close expired jobs
- Notification when job expires or approval is needed
- JD template apply → call `/apply/` endpoint for usage tracking (currently fills fields client-side)
