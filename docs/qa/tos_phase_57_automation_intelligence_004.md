# TOS Phase 57: Automation Intelligence 004 — Learning Engine

## Objective
Implement the Automation Learning Engine: a background service that analyses
per-policy suggestion outcome metrics and creates actionable
`AISuggestion` records that recommend automation configuration improvements
to tenant admins.

## Context
- Policy model, evaluator pipeline, and UI delivered in docs 001–003.
- Automation analytics (`AutomationAnalyticsService`, `/intelligence/automation-analytics/`)
  delivered in Step 6 (prerequisites for this step).
- This step adds learning logic on top of the analytics layer.

---

## New Suggestion Categories

Two new values added to `SuggestionCategory` in
`apps/orchestration_center/constants/execution_statuses.py`:

| Value | Label |
|-------|-------|
| `policy_improvement` | Policy Improvement |
| `automation_recommendation` | Automation Recommendation |

These categories appear alongside existing categories in the Suggestions section
of Intelligence Hub.  The frontend `SuggestionsSection` requires no changes —
the new categories are displayed using the existing `humanize()` helper and the
existing "Automation Recommendation" label surfaces naturally.

---

## Backend

### `PolicyMetrics` dataclass

**File:** `services/automation_learning_service.py`

Computed per-policy over the trailing 30-day window:

| Property | Formula |
|----------|---------|
| `total_decided` | `approved + rejected` |
| `approval_rate` | `approved / total_decided × 100` |
| `rejection_rate` | `rejected / total_decided × 100` |
| `apply_success_rate` | `applied / (applied + apply_failed) × 100` |

Module scope handling: if `policy.module_scope` is non-empty, the query filters
`AISuggestion.source_module` to that value; otherwise all modules are included.

---

### `LearningEvaluator`

**File:** `services/automation_learning_service.py`

Stateless evaluator.  Accepts a `PolicyMetrics` object and an ISO-week string
and returns a list of `LearningRecommendation` dataclass instances.

#### Learning Rules

| Rule key | Category | Condition | Min sample |
|----------|----------|-----------|-----------|
| `enable_auto_approve` | `automation_recommendation` | `approval_rate > 90%` AND `auto_approve = False` | `total_decided ≥ 5` |
| `enable_auto_apply` | `automation_recommendation` | `apply_success_rate > 95%` AND `auto_apply = False` | `applied ≥ 3` |
| `disable_auto_approve` | `policy_improvement` | `approval_rate < 30%` AND `auto_approve = True` | `total_decided ≥ 5` |
| `high_rejection_rate` | `policy_improvement` | `rejection_rate > 70%` AND `auto_approve = False` | `total_decided ≥ 5` |

#### Confidence scores

| Rule | Score formula | Cap |
|------|--------------|-----|
| `enable_auto_approve` | `approval_rate / 100 × 1.05` | 0.99 |
| `enable_auto_apply` | `apply_success_rate / 100 × 1.02` | 0.97 |
| `disable_auto_approve` | fixed `0.85` | — |
| `high_rejection_rate` | fixed `0.75` | — |

#### Idempotency key format

```
learning:{policy_id}:{rule_key}:{iso_week}
```

e.g. `learning:abc-123:enable_auto_approve:2026-W14`

One learning suggestion is created per (policy × rule) per ISO calendar week.

---

### `AutomationLearningService`

**File:** `services/automation_learning_service.py`

| Method | Description |
|--------|-------------|
| `run_for_tenant(tenant_id)` | Evaluates all enabled policies for a single tenant; returns summary dict |
| `run_for_all_tenants()` | Iterates over all tenants with at least one enabled policy |
| `_collect_metrics(policy)` | Queries `AISuggestion` in the 30-day window; returns `PolicyMetrics` |
| `_persist_recommendation(tenant_id, rec)` | Creates `AISuggestion`, returns `id` or `None` if idempotency key exists |

#### `run_for_tenant` return value

```json
{
  "tenant_id": "<uuid>",
  "policies_evaluated": 3,
  "suggestions_created": 2,
  "suggestions_skipped_idempotent": 1,
  "suggestion_ids": ["<uuid>", "<uuid>"]
}
```

#### Created `AISuggestion` fields

| Field | Value |
|-------|-------|
| `category` | `automation_recommendation` or `policy_improvement` |
| `suggestion_key` | Rule key (e.g. `enable_auto_approve`) |
| `source_module` | `automation_learning_engine` |
| `source_event` | `learning.policy_analysis` |
| `source_entity_type` | `automation_intelligence_policy` |
| `source_entity_id` | Policy UUID |
| `proposed_action_family` | `policy_configuration` |
| `status` | `pending` |
| `requires_approval` | `False` |
| `manual_override_allowed` | `True` |
| `idempotency_key` | ISO-week scoped key (see above) |
| `payload_json` | `{policy_id, rule_key, suggestion_type, module_scope}` |

---

### Celery Tasks

**File:** `tasks/automation_intelligence_tasks.py`

| Task name | Trigger | Description |
|-----------|---------|-------------|
| `run_automation_learning_hourly` | `crontab(minute=0)` | Lightweight pass over all tenants |
| `run_automation_learning_daily` | `crontab(hour=2, minute=0)` | Comprehensive daily pass at 02:00 UTC |

Idempotency keys prevent duplicate suggestions even when both tasks run within
the same ISO week.

**Beat schedule snippet (add to Django settings):**

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'automation-learning-hourly': {
        'task': 'run_automation_learning_hourly',
        'schedule': crontab(minute=0),
    },
    'automation-learning-daily': {
        'task': 'run_automation_learning_daily',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

---

## UI — Suggestions Section

Learning suggestions are plain `AISuggestion` records and surface in the
existing **Intelligence Hub → Suggestions** section without any frontend changes.

Recognisable by:
- `category` = `automation_recommendation` or `policy_improvement`
- `source_module` = `automation_learning_engine`
- Title examples:
  - "Enable auto-approve for followup recommendation (all modules)"
  - "Enable auto-apply for deadline recommendation (pipeline)"
  - "Review auto-approve for escalation recommendation (all modules)"
  - "High rejection rate for communication draft (all modules) — review policy"

Tenant admins can approve, dismiss, or reject these suggestions through the
existing suggestion action buttons.

---

## Test Coverage

**File:** `tests/test_automation_learning.py`

### `LearningEvaluatorTests`

| Test | Description |
|------|-------------|
| `test_no_rules_fire_on_insufficient_sample` | Below `MIN_SAMPLE_DECIDED=5` → no recommendations |
| `test_enable_auto_approve_fires_above_threshold` | `approval_rate=90.9%` fires rule; category and confidence verified |
| `test_enable_auto_approve_does_not_fire_at_boundary` | Exactly 90.0% — rule requires `> 90%`, so no fire |
| `test_enable_auto_approve_suppressed_when_already_enabled` | `auto_approve=True` suppresses rule |
| `test_enable_auto_apply_fires_above_threshold` | 100% apply success → fires |
| `test_enable_auto_apply_does_not_fire_below_threshold` | 95.0% — requires `> 95%` |
| `test_enable_auto_apply_requires_min_sample` | Only 2 applied (below `MIN_SAMPLE_APPLIED=3`) → no fire |
| `test_disable_auto_approve_fires_on_low_approval_rate` | 20% with `auto_approve=True` → `policy_improvement` |
| `test_disable_auto_approve_not_fire_above_threshold` | 40% → no fire |
| `test_high_rejection_rate_fires` | 80% rejection → `policy_improvement` |
| `test_idempotency_keys_are_unique_per_rule` | All returned keys are unique |
| `test_multiple_rules_can_fire_simultaneously` | Both `enable_auto_approve` + `enable_auto_apply` fire |

### `AutomationLearningServiceTests`

| Test | Description |
|------|-------------|
| `test_no_suggestions_created_for_empty_policy` | Zero suggestion history → nothing created |
| `test_high_approval_rate_creates_auto_approve_suggestion` | 10/11 approved → suggestion created with correct fields |
| `test_high_apply_success_rate_creates_auto_apply_suggestion` | 10/10 applied → auto-apply suggestion |
| `test_low_approval_rate_on_auto_approved_policy_creates_policy_improvement` | 2/10 approved → `policy_improvement` |
| `test_idempotency_prevents_duplicate_suggestions` | Second run produces 0 new, `skipped_idempotent ≥ 1` |
| `test_tenant_isolation` | Tenant A data does not create suggestions for Tenant B |
| `test_disabled_policy_is_skipped` | `is_enabled=False` → skipped |
| `test_module_scope_filter_applied` | Suggestions from wrong module don't count toward scoped policy |
| `test_run_for_all_tenants_processes_multiple_tenants` | Both tenants processed; totals correct |
| `test_learning_suggestions_have_correct_fields` | All required AISuggestion fields verified |

---

## Validation

```bash
# Run learning engine tests
python3 backend/manage.py test \
  apps.orchestration_center.tests.test_automation_learning -v 2

# Run full automation intelligence test suite
python3 backend/manage.py test \
  apps.orchestration_center.tests.test_automation_intelligence \
  apps.orchestration_center.tests.test_automation_learning \
  apps.orchestration_center.tests.test_suggestion_engine -v 1

# Trigger manually in Django shell
python3 backend/manage.py shell -c "
from apps.orchestration_center.services.automation_learning_service import AutomationLearningService
import uuid
# Replace with a real tenant UUID
result = AutomationLearningService.run_for_tenant(uuid.UUID('<tenant-uuid>'))
print(result)
"
```
