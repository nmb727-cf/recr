# TOS Phase 57: Automation Intelligence 002 — UI Panel & Template Library

## Objective
Build the Automation Intelligence UI panel inside Intelligence Hub (Step 4) and
the Automation Intelligence Library — a reusable template system for
instantiating policies without manual configuration (Step 5).

## Context
- `AutomationIntelligencePolicy` model, CRUD views, and evaluator pipeline
  were delivered in `tos_phase_57_automation_intelligence_001.md`.
- Step 4 adds the policy management UI panel, URL aliases, and full CRUD test coverage.
- Step 5 adds the `AutomationTemplate` model, library endpoints, and Template Library UI section.

---

## Step 4 — Automation Intelligence UI Panel

### Backend Changes

#### URL aliases (`api/urls.py`)
Two short-form URL aliases added alongside the canonical routes:

| Alias | Canonical | View |
|-------|-----------|------|
| `GET/POST /intelligence/automation-policies/` | `/intelligence/automation-intelligence/policies/` | `AutomationIntelligencePolicyListCreateView` |
| `GET/PUT/DELETE /intelligence/automation-policies/{id}/` | `/intelligence/automation-intelligence/policies/{id}/` | `AutomationIntelligencePolicyDetailView` |

Named routes: `intelligence-automation-policy-list-create`,
`intelligence-automation-policy-detail`.

Both canonical and alias routes share the same views, serializer, permission
checks, tenant scoping, and audit logging.

#### Serializer fix
`IntelligenceAuditLog` was referenced in `IntelligenceAuditLogSerializer` but
missing from the model import block — added to `serializers.py` import.

### Frontend API Client (`api/intelligenceHub.ts`)

Four alias methods added at the new short-form URL:

```typescript
listAutomationPolicies()
createAutomationPolicy(payload)
updateAutomationPolicy(id, payload)
deleteAutomationPolicy(id)
```

### Intelligence Hub UI — Automation Intelligence Section

**Location:** `pages/intelligence/IntelligenceHubWorkspace.tsx`
**Section key:** `automation-intelligence`
**Navigation label:** "Automation Intelligence"

#### Table columns
| Column | Content |
|--------|---------|
| Suggestion Type | Humanized category |
| Module Scope | Scope string or "All modules" |
| Automation Level | Native `<select>` (`suggest_only` / `auto_approve` / `auto_apply`) |
| Confidence Threshold | Editable number input per row |
| Enabled | Toggle switch per row (`data-testid="automation-intelligence-enabled-{id}"`) |
| Actions | Save + Delete buttons per row |
| Last Outcome | Last policy evaluation result |
| Updated | Timestamp |

#### Create form
Fields rendered above the table:

| Field | Control | `data-testid` |
|-------|---------|---------------|
| Suggestion Type | Native `<select>` | `automation-intelligence-new-type` |
| Module Scope | Text input | `automation-intelligence-new-module` |
| Confidence Threshold | Range slider (`type="range"` 0–1, step 0.01) with live value display | `automation-intelligence-new-threshold` |
| Automation Level | Native `<select>` | `automation-intelligence-new-level` |
| Enabled | Ant Design Switch | — |
| Submit | "Add Policy" button | — |

#### Row editing
Each row is independently editable. The Automation Level select, threshold
input, and enabled switch update local draft state (`draftById`). Clicking
**Save** calls `updateAutomationIntelligencePolicy(id, { ...flags })`.
Clicking **Delete** calls `deleteAutomationIntelligencePolicy(id)`.

Level → flag mapping:

| Level | `auto_approve` | `auto_apply` | `approval_required` |
|-------|---------------|-------------|---------------------|
| `suggest_only` | false | false | true |
| `auto_approve` | true | false | true |
| `auto_apply` | true | true | false |

#### Permissions
- View: `automation_intelligence.view`
- Create / Update / Delete: `automation_intelligence.manage` (tenant admin only)

#### Real-time refresh
Query key: `['intelligence-hub', 'automation-intelligence-policies']`

---

## Step 5 — Automation Intelligence Library (Templates)

### Model (`AutomationTemplate`)

**File:** `apps/orchestration_center/models/automation_intelligence.py`
**Migration:** `0005_automationtemplate.py`
**Table:** `icc_automation_templates`

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID PK | |
| `tenant_id` | UUID nullable | `null` for builtin platform templates |
| `name` | CharField(255) | |
| `description` | TextField | optional |
| `suggestion_type` | CharField(64) | `SuggestionCategory` choices |
| `module_scope` | CharField(64) | blank = all modules |
| `automation_level` | CharField(20) | `suggest_only` / `auto_approve` / `auto_apply` |
| `confidence_threshold` | Decimal(5,2) | 0.00–1.00, default 0.85 |
| `is_builtin` | BooleanField | platform-managed; read-only for tenants |
| `tags` | JSONField | list of strings for filtering |
| standard BaseModel fields | | `created_at`, `updated_at`, `created_by`, `is_deleted`, `metadata` |

**Scoping rule:** `GET` returns `is_builtin=True AND tenant_id IS NULL` UNION
tenant's own custom templates. Built-in templates cannot be modified or deleted.

### Backend Endpoints

| Method | URL | View | Permission |
|--------|-----|------|-----------|
| `GET` | `/intelligence/automation-templates/` | `AutomationTemplateListCreateView` | `automation_templates.view` |
| `POST` | `/intelligence/automation-templates/` | `AutomationTemplateListCreateView` | `automation_templates.manage` |
| `GET` | `/intelligence/automation-templates/{id}/` | `AutomationTemplateDetailView` | `automation_templates.view` |
| `PUT` | `/intelligence/automation-templates/{id}/` | `AutomationTemplateDetailView` | `automation_templates.manage` (custom only) |
| `DELETE` | `/intelligence/automation-templates/{id}/` | `AutomationTemplateDetailView` | `automation_templates.manage` (custom only) |
| `POST` | `/intelligence/automation-templates/{id}/apply/` | `AutomationTemplateApplyView` | `automation_intelligence.manage` |

Named routes: `intelligence-automation-template-list-create`,
`intelligence-automation-template-detail`, `intelligence-automation-template-apply`.

#### Apply endpoint
Creates an `AutomationIntelligencePolicy` from the template's parameters using
the standard level → flag mapping. Emits audit log entry with
`action_type='automation_intelligence_policy.created_from_template'` and
`source_template_id` in `after_state`.

#### Permissions registered
`automation_templates.view` — all authenticated roles.
`automation_templates.manage` — `super_admin`, `tenant_admin`.

### Serializer

`AutomationTemplateSerializer` in `serializers.py`:
- `read_only_fields`: `id`, `created_at`, `updated_at`, `created_by`, `is_builtin`
- Validates `confidence_threshold` is between 0.00 and 1.00.

### Frontend API Client (`api/intelligenceHub.ts`)

Five new methods:

```typescript
listAutomationTemplates(params?: { suggestion_type?: string; automation_level?: string })
createAutomationTemplate(payload)
updateAutomationTemplate(id, payload)
deleteAutomationTemplate(id)
applyAutomationTemplate(id)
```

### Intelligence Hub UI — Template Library Section

**Location:** `pages/intelligence/IntelligenceHubWorkspace.tsx`
**Section key:** `automation-template-library`
**Navigation label:** "Template Library"
**Route:** `/intelligence/automation-template-library`

#### Table columns
| Column | Content |
|--------|---------|
| Name | Template name + "Built-in" badge if `is_builtin` |
| Description | Description text |
| Suggestion Type | Humanized category tag |
| Module Scope | Scope string or "All modules" |
| Level | Colored tag — default / purple / cyan for suggest_only / auto_approve / auto_apply |
| Threshold | Two-decimal display |
| Actions | Apply button (`data-testid="automation-template-apply-{id}"`); Delete button for custom only (`data-testid="automation-template-delete-{id}"`) |

#### Create form (custom templates)
Rendered above the table, visible to all; write enforced at API level.

| Field | Control | `data-testid` |
|-------|---------|---------------|
| Name | Text input | `automation-template-new-name` |
| Description | Text input | `automation-template-new-description` |
| Suggestion Type | Native `<select>` | `automation-template-new-type` |
| Module Scope | Text input | `automation-template-new-module` |
| Automation Level | Native `<select>` | `automation-template-new-level` |
| Confidence Threshold | Range slider (0–1, step 0.01) with live label | `automation-template-new-threshold` |
| Submit | "Add Template" button | `automation-template-create-btn` |

#### Query key
`['intelligence-hub', 'automation-templates']`

#### Sidebar navigation
Entry added to `intelligence-hub` group in both `companySidebarConfig` and
`agencySidebarConfig` in `navigation.tsx`:
```tsx
{ key: '/intelligence/automation-template-library', label: 'Template Library', icon: <LayoutGridOutlined /> }
```

## Validation

```bash
# Backend
python3 backend/manage.py migrate orchestration_center
python3 backend/manage.py test \
  apps.orchestration_center.tests.test_automation_intelligence -v 1

# Frontend
npm test -- --run src/pages/intelligence/IntelligenceHubWorkspace.test.tsx
```
