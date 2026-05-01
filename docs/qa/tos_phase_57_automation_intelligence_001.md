# TOS Phase 57: Automation Intelligence 001

## Objective
- introduce AI-driven workflow automation on top of governed suggestions
- keep governance boundaries intact while enabling controlled auto-approve/auto-apply
- make policy controls visible and configurable from Intelligence Hub UI

## Architecture
- new tenant-scoped policy model: `AutomationIntelligencePolicy`
- async execution path:
  - suggestion created in `SuggestionService`
  - on-commit enqueue: `evaluate_suggestion_policy_task`
  - task delegates to `AutomationIntelligenceService.evaluate_suggestion_policy`
  - service is a thin façade over `SuggestionPolicyEvaluator.evaluate()`
- policy evaluation is non-blocking and audit-backed
- orchestration remains orchestration-only; owner module contracts are still used for apply

## Automation Tiers
- Level 1: `suggest_only`
  - no auto-approve
  - no auto-apply
- Level 2: `auto_approve`
  - auto-approve when confidence and scope rules match
  - no auto-apply
- Level 3: `auto_apply` (restricted)
  - requires explicit policy configuration
  - enforces `auto_approve=true` and `approval_required=false`
  - apply still uses owner-module contract and remains non-blocking
  - must pass `AutoApplyGuard` before apply is attempted

## Policy Model
Fields:
- `suggestion_type`
- `module_scope`
- `confidence_threshold`
- `auto_approve`
- `auto_apply`
- `approval_required`
- `is_enabled`
- `priority_order`
- tenant-scoped metadata (`tenant_id`, audit timestamps, last outcome fields)

## AutoApplyGuard

**Location:** `apps/orchestration_center/services/suggestion_policy_evaluator.py`

**Purpose:** determines whether a suggestion is safe to auto-apply before the
evaluator calls `SuggestionService.apply_suggestion`.

**Two-gate model:**

| Gate | Condition | Blocked reason |
|------|-----------|----------------|
| Manual override | `suggestion.manual_override_allowed` must be `True` | `manual_override_not_allowed` |
| Category allowlist | `suggestion.category` must be in `SAFE_CATEGORIES` | `category_blocked:<cat>` or `category_not_in_safe_list:<cat>` |

**Safe categories** (auto-apply permitted):
```
followup_recommendation
deadline_recommendation
notify_recommendation
review_task_recommendation
communication_draft
```

**Blocked categories** (auto-apply explicitly prohibited):
```
stage_change
rejection
offer_creation
candidate_assignment
deletion
```

Any category not in either list is treated as blocked (`category_not_in_safe_list`).
Unknown future categories default to blocked until explicitly promoted.

**Interface:**
```python
is_safe, blocked_reason = AutoApplyGuard.check(suggestion)
# blocked_reason is None when safe
```

## Policy Evaluation Logic (`SuggestionPolicyEvaluator`)

**Location:** `apps/orchestration_center/services/suggestion_policy_evaluator.py`

**Classes exported:**
- `PolicyEvaluationResult` — dataclass:
  `status`, `suggestion_id`, `policy_id`, `auto_approved`, `auto_applied`,
  `outcome`, `blocked_reason`; `.as_dict()` also includes `auto_apply_blocked_reason`
  as an alias of `blocked_reason`
- `AutoApplyGuard` — category-based safety gate
- `SuggestionPolicyEvaluator` — evaluator with `evaluate(suggestion_id) -> PolicyEvaluationResult`

**Evaluation flow:**
1. Lock suggestion row (`SELECT FOR UPDATE`).
2. Guard: skip if missing or not `pending`.
3. Resolve highest-priority matching policy:
   - `tenant_id` match, `is_enabled=True`, `suggestion_type` match
   - `confidence_threshold` ≤ `confidence_score`
   - module-scoped policies preferred over global ones
4. No policy → `no_matching_policy`.
5. Propagate `approval_required` to suggestion if policy sets it.
6. `policy.auto_approve` → `SuggestionService.approve_suggestion` → `auto_approved=True`.
7. `policy.auto_apply`:
   - `AutoApplyGuard.check(suggestion)` fails → outcome `auto_apply_blocked`,
     `blocked_reason` set; suggestion left `approved`.
   - Guard passes and suggestion is `approved` → `SuggestionService.apply_suggestion`.
   - Apply fails (`OwnerContractError`) → outcome `auto_apply_failed`, non-blocking.
8. Update `policy.last_triggered_at`, `last_outcome`, `last_triggered_suggestion_id`.
9. Emit `ai_suggestion.automation_policy_evaluated` audit event with:
   `policy_id`, `auto_approve`, `auto_apply`, `confidence_threshold`, `outcome`,
   `auto_approved`, `auto_applied`, `blocked_reason`, `auto_apply_blocked_reason`.

## Runtime Hook

**Location:** `SuggestionService.create_suggestion` (line ~356)

```python
if created:
    SuggestionService._schedule_automation_intelligence_evaluation(suggestion_id=suggestion.id)
```

Registers a `transaction.on_commit` callback that calls
`evaluate_suggestion_policy_task.delay(str(suggestion_id))`.

**Task:** `evaluate_suggestion_policy_task` (Celery, `max_retries=1`)
- Calls `AutomationIntelligenceService.evaluate_suggestion_policy`
- Logs errors to audit trail on unexpected exceptions
- Never raises — failures are audit-logged and returned as a status dict

## Auto-Approval Behavior

When `policy.auto_approve=True` and confidence ≥ threshold:
- suggestion: `pending → approved`
- `approval_comment` = `Auto-approved by automation intelligence policy {policy.id}`
- audit: `ai_suggestion.approved` + `ai_suggestion.automation_policy_evaluated`
  with `auto_approved=True`

## Auto-Apply Behavior

When `policy.auto_apply=True`, guard passes, and suggestion is `approved`:
- suggestion: `approved → applied` (or `apply_failed` on contract error)
- `apply_comment` = `Auto-applied by automation intelligence policy {policy.id}`
- apply uses owner-module contract (same path as manual apply)
- failure is non-blocking: outcome `auto_apply_failed`, suggestion `apply_failed`
- guard rejection: outcome `auto_apply_blocked`, suggestion stays `approved`

## Intelligence Hub UI — Auto Badges (Suggestions table)

The Status column shows supplementary badges when a suggestion was acted upon
by the automation engine:

| Badge | Detection |
|-------|-----------|
| **Auto Approved** (purple) | `approval_comment` starts with `"Auto-approved"` |
| **Auto Applied** (cyan) | `apply_comment` starts with `"Auto-applied"` |

These badges are additive — they appear alongside the primary status tag.

## Backend Endpoints
- `GET /api/v1/intelligence/automation-intelligence/policies/`
- `POST /api/v1/intelligence/automation-intelligence/policies/`
- `GET /api/v1/intelligence/automation-intelligence/policies/{id}/`
- `PUT /api/v1/intelligence/automation-intelligence/policies/{id}/`
- `DELETE /api/v1/intelligence/automation-intelligence/policies/{id}/`

Permissions:
- view: `automation_intelligence.view`
- manage: `automation_intelligence.manage`

## Safety Rules Enforced
- tenant isolation on policy CRUD and evaluation
- module scoping support (`module_scope` exact match or global scope)
- governance override remains active (`approval_required` can be preserved)
- full audit events for policy CRUD and evaluation outcomes
- non-blocking failure behavior for apply path
- disabled policies (`is_enabled=False`) filtered at query time
- `manual_override_allowed=False` blocks auto_apply regardless of policy
- category allowlist: only explicitly safe categories are auto-applied
- unknown / future categories default to blocked

## Test Coverage
Backend (`apps.orchestration_center.tests.test_automation_intelligence` — 9 cases):
- policy CRUD permission + tenant isolation
- auto-approve when threshold matches
- auto-apply configured (mocked apply execution)
- threshold enforcement / fallback to no_matching_policy
- disabled policy skipped (`is_enabled=False`)
- auto_apply blocked when `manual_override_allowed=False`
- safe category (`followup_recommendation`) auto-applies successfully
- blocked category (`escalation_recommendation`) prevents auto_apply
- apply failure is non-blocking (`OwnerContractError` → `auto_apply_failed`)
- async policy scheduling on suggestion creation

Frontend (`IntelligenceHubWorkspace.test.tsx` — 2 badge cases + 38 existing):
- Auto Approved badge renders for auto-approved suggestion
- Auto Applied badge renders for auto-applied suggestion

## Current Limitations
- no batch policy operations yet
- no per-policy RBAC override beyond hub permission role map
- no separate retry endpoint for policy-triggered auto-apply failures

## Validation
- backend:
  - `python3 backend/manage.py test apps.orchestration_center.tests.test_suggestion_engine apps.orchestration_center.tests.test_automation_intelligence -v 1`
- frontend:
  - `npm test -- --run src/pages/intelligence/IntelligenceHubWorkspace.test.tsx`
