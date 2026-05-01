# V1 Audit: Company Onboarding + Company Settings

## Scope
This audit covers V1 company onboarding and company settings surfaces across organisation setup, departments/teams/locations, members, RBAC, configuration, and integrations.

This is an audit only. No implementation recommendations beyond product-level redesign priorities.

---

## 1) File / Structure Audit

### Backend files reviewed
- `backend/apps/accounts/views.py`
  - Company onboarding completion API (`/auth/onboarding/complete/`), preference persistence, automation bootstrap.
- `backend/apps/accounts/serializers.py`
  - Onboarding payload schema (hiring style/team size/automation preference).
- `backend/apps/organisations/models.py`
  - Data models for Organisation, Department, Location, Team, TeamMembership.
- `backend/apps/organisations/serializers.py`
  - Thin serializers for org entities.
- `backend/apps/organisations/views.py`
  - CRUD APIs for organisation profile, departments, locations, teams, team members, users.
- `backend/apps/organisations/urls.py`
  - Org/settings endpoint registry.
- `backend/apps/rbac/models.py`
  - Permission/Role/RolePermission model design.
- `backend/apps/rbac/views.py`
  - Role catalog, create/clone/update/delete tenant roles.
- `backend/apps/rbac/permissions.py`, `backend/apps/rbac/utils.py`
  - Permission enforcement factory and runtime permission resolution/cache.
- `backend/apps/integrations/models.py`, `views.py`, `serializers.py`, `urls.py`
  - Generic integrations CRUD.
- `backend/apps/communications/urls.py`
  - Email account + notification control + channel control endpoints.
- `backend/apps/communications/permissions.py`
  - RBAC permission mappings for communication module.
- `backend/apps/communications/models.py`
  - Email account/credentials and communication configuration models.
- `backend/apps/communications/email_accounts/views.py`, `services.py`
  - OAuth/SMTP connect flows, encrypted credential persistence, account health.
- `backend/apps/communications/notification_control_views.py`
  - Notification rule and channel settings control APIs.
- `backend/apps/communications/notification_orchestration_views.py`
  - Admin/debug orchestration controls.

### Frontend files reviewed
- `frontend/src/pages/onboarding/OnboardingWizard.tsx`
  - Company/agency setup wizard after email verification.
- `frontend/src/pages/onboarding/CompanyOnboarding.tsx`
  - Organisation setup/edit page and setup completeness behavior.
- `frontend/src/components/common/OnboardingGuard.tsx`
  - Runtime gate forcing onboarding completion before app usage.
- `frontend/src/pages/Settings.tsx`
  - Main settings page: profile, departments, locations, users, roles, communication, account.
- `frontend/src/pages/organisation/IntegrationHub.tsx`
  - Integration marketplace-like page.
- `frontend/src/api/organisation.ts`
  - Organisation/users/departments/locations client.
- `frontend/src/api/rbac.ts`
  - RBAC role catalog + mutation client.
- `frontend/src/api/integrations.ts`
  - Generic integrations client.
- `frontend/src/api/communications.ts`
  - Email integration/control clients.
- `frontend/src/App.tsx`
  - Route-level separation between onboarding, settings, integrations, and protected roles.

### Separation: Onboarding vs Settings
- Onboarding is split into 2 tracks:
  - `OnboardingWizard` (hiring preferences + optional email connect) -> `/onboarding/wizard`.
  - `CompanyOnboarding` (org profile form) -> `/company-onboarding`.
- Settings is a separate monolithic page (`Settings.tsx`) with tabs for profile/departments/locations/users/roles/communication/account.
- Real-world overlap is high: org profile setup appears in both onboarding and settings, creating duplicated behavior and duplicated validation assumptions.

---

## 2) Onboarding Flow (Company)

### Steps and sequencing
1. User signs up as company (`tenant_admin`).
2. Email verification.
3. Redirect to `/onboarding/wizard` for preference capture.
4. Wizard submits:
   - `hiring_style`
   - `team_size`
   - `automation_preference`
5. Backend marks onboarding complete in user/org metadata and creates default automation rules.
6. Wizard may optionally trigger email-provider OAuth connect; otherwise navigates dashboard.
7. `OnboardingGuard` later checks org metadata and candidate/profile completeness to enforce gate.

### Data collected
- Wizard forced fields: one choice each for hiring style, team size, automation preference.
- Optional final step: connect Gmail/Outlook or skip.
- CompanyOnboarding forced fields: org name, country, timezone, industry.
- CompanyOnboarding optional fields: website, size_range.

### Branching logic
- Wizard path derived by role (company vs agency variants).
- `user_type` derived server-side from role mapping (not user-selected).
- If org metadata not marked complete, guard redirects to onboarding wizard.

### Defaults/auto-generated
- Auto defaults include:
  - `country_code`/`timezone` prefill behavior.
  - reference prefix auto-generation in tenant layer.
- Auto-generated backend behavior:
  - Automation rules based on preference.
  - `metadata.onboarding_completed` marker.

### Critical observation
- Company onboarding is partially duplicated:
  - Wizard handles hiring preferences.
  - CompanyOnboarding handles org identity fields.
  - Settings profile tab handles many of same org fields again.
- This is fragmented setup, not a unified onboarding journey.

---

## 3) Organization Model

### Company profile fields
- `Organisation`: name, org_type, website, logo, industry, size_range, country_code, timezone, address/legal fields, settings JSON, metadata JSON.

### Department structure
- `Department`: name, parent_department_id, head_user_id, description, metadata.
- Hierarchy technically supported via `parent_department_id`.

### Team structure
- `Team`: name, department_id, location_id, team_lead_id, description.
- `TeamMembership`: team + user + role.

### Flat vs hierarchical
- Data model supports hierarchy (department parent pointers).
- UI does not operationalize hierarchy meaningfully.
- Team/dept objects are mostly CRUD containers with little policy/workflow semantics.

### Enterprise scalability assessment
- Model has enterprise-like field placeholders.
- Product behavior is mostly lightweight CRUD with weak orchestration.
- Net: structurally promising, operationally shallow.

---

## 4) Members + RBAC

### Role system
- Fixed base roles exist (`tenant_admin`, `recruiter`, etc.).
- Tenant custom roles supported through RBAC role catalog and permission selection.

### Permission system
- Permission codes (`module.resource.action`) with role-permission mapping.
- Runtime permission cache per user.
- `require_permission()` helper for DRF views.

### Assignment logic
- Settings Users tab updates `CustomUser.role` directly.
- Role creation/editing in Roles tab allows custom permission bundles.

### Granularity and separation of duties
- RBAC infrastructure is relatively deep for template/custom role management.
- But key organisation endpoints (`organisations/views.py`) are mostly `IsAuthenticated` only.
- That means core settings operations are not consistently enforced through RBAC permissions.

### Critical mismatch
- Strong RBAC model exists.
- Enforcement is inconsistent in high-impact admin APIs.
- Product presents enterprise RBAC surface but backend authorization depth is uneven.

---

## 5) Locations

### Location model
- `Location`: name + address/city/state/country/postal + lat/long + HQ flag + metadata.

### Multi-location handling
- Backend supports multiple locations per tenant.
- Teams can reference a location via `location_id`.

### Geo-based hiring support
- Foundational fields exist (lat/long, HQ, country/city).
- No deep geo policy or compliance workflow discovered in settings/onboarding surfaces.

### Normalization/scalability
- Reasonably normalized for base CRUD.
- Missing operational constructs (regional hiring policy layers, legal entity-to-location rules, location-level permissions).

---

## 6) Settings / Configuration

### What settings exist
- Organisation profile: brand/region/currency/reference prefix/basic company details.
- Departments.
- Locations.
- Users (invite/update/delete).
- Roles & permissions editor.
- Communication/email controls.
- Account security/localization.

### What is configurable
- Org profile fields and some nested `settings.default_currency`.
- Department/location CRUD.
- User role/status management.
- Tenant custom RBAC roles.
- Email provider connect/default sender/fallback behavior.

### Hardcoded/weakly-modeled areas
- Many business defaults hardcoded in frontend flows.
- Some settings appear in UI but are not strongly validated by backend schema (or inconsistent with model fields).
- No obvious robust settings schema/versioning governance for organization policy.

### Product depth callout
- Large settings surface area, but much of it is “basic CRUD + few fields” without deep policy logic.

---

## 7) Integrations

### Covered integrations
- Generic `integrations` module (provider_key/category/status/config_json).
- Communication/email integrations via dedicated communications module:
  - Gmail OAuth
  - Microsoft OAuth
  - SMTP

### Structure quality
- Generic integrations module is thin and mostly status/config storage.
- Email integrations are significantly more mature:
  - OAuth state handling
  - callback completion
  - encrypted credential storage fields
  - account health and audit events

### Credentials and data flow
- OAuth/SMTP secrets stored in encrypted fields (`*_encrypted`).
- OAuth state stored with TTL cache; callbacks validate state.
- Frontend to backend redirect orchestration exists with post-connect status handling.

### Gaps
- IntegrationHub UI behaves like marketplace toggles/config modal, but appears partly disconnected from enterprise-grade backend workflows.
- Non-email integrations look mostly superficial configuration records, not complete integration lifecycles.

---

## 8) Workflows

### Onboarding workflow
- Role-based wizard -> backend onboarding metadata + automation defaults + optional connect.

### Org setup workflow
- CompanyOnboarding setup completion heuristic and redirect logic.
- Settings profile can also modify setup fields.

### Approval/workflow depth
- No strong approval workflow for org structure changes, role changes, or integration changes in core settings.
- Notification orchestration admin endpoints exist but are separate operational controls.

### Frontend vs backend logic split
- Too much orchestration logic in frontend components (tab-level behavior, setup completeness assumptions, local branching).
- Backend endpoints often act as passive CRUD rather than policy engines.

---

## 9) Security

### RBAC enforcement
- Strong in communication module (permission classes).
- Weak/partial in organisations module (mostly auth-only).

### Tenant isolation
- Most org APIs filter by `request.user.tenant_id`, which is good baseline isolation.
- Still relies heavily on application-layer filters with UUID linkage across models.

### Sensitive data handling
- Email integration credentials stored encrypted.
- OAuth state flow includes nonce-like state + expiry.

### Risks
- Critical admin operations can be reachable by any authenticated tenant user if route access isn’t tightly gated at API level.
- Frontend role gating is not a substitute for backend authorization.

---

## 10) UX / Product Depth

### Onboarding experience
- Wizard is clean and low-friction.
- But onboarding is fragmented across wizard + company onboarding + settings profile.

### Settings usability
- Single mega page (`Settings.tsx`) mixes many domains.
- Broad functionality but uneven consistency and depth.

### Cognitive load
- Medium-high: many unrelated controls in one settings surface.
- Role/permission editing is powerful but can overwhelm non-technical admins.

### Enterprise vs basic
- Feels enterprise in breadth, not in governance depth.
- Significant portions are still basic CRUD + presentation polish.

### What V1 does better than V2 (from this module evidence)
- RBAC role catalog UX is more explicit.
- Email communications integration/health model is materially deeper than simple toggle-based approaches.

### What is confusing
- Overlap between onboarding and settings for org profile.
- Team APIs exist but are not clearly surfaced in core settings UI.
- IntegrationHub promises broad marketplace depth, but most providers appear non-operational placeholders.

---

## 11) Strengths

- Clear tenant-scoped organisation data domain.
- Good foundational org schema (departments/teams/locations and metadata support).
- RBAC model supports system templates + tenant custom roles.
- Communication/email integration path includes real operational concerns (health, fallback, audit, OAuth callback discipline).
- Onboarding auto-configuration creates initial automation momentum.

---

## 12) Weaknesses

- **Architecture**: duplicated onboarding vs settings responsibilities.
- **Authorization inconsistency**: RBAC model exists, but many org endpoints use only `IsAuthenticated`.
- **Product cohesion**: settings page is monolithic and domain-mixed.
- **Operational realism**: several areas are CRUD shells without enterprise workflow semantics.
- **Integration depth mismatch**: email is deep; many other integrations look shallow.

---

## 13) Missing Enterprise Depth

### Fields/structure
- Missing richer legal-entity/business-unit mapping beyond basic org/dept/team fields.
- No robust policy layers for location-level governance.

### Workflows
- No structured approval flow for role changes, org changes, integration changes.
- No formal setup stage model/versioning for onboarding progression.

### Validations
- Inconsistent backend validation depth for settings entities.
- UI fields include assumptions not strongly reflected in backend schema constraints.

### Automation
- Limited admin automation around org setup maintenance, data quality checks, and governance triggers.

### UI capabilities
- Team management capability exists backend-side but not clearly integrated into primary settings workflow.
- Weak cross-entity orchestration (department-head assignment, location ownership policies, etc.).

### Intelligence
- Limited decision support around org design, access risk, config drift, integration health beyond basic status displays.

---

## 14) Impact

### Recruiter impact
- Gets usable baseline settings quickly.
- Suffers when org policy logic is needed beyond simple CRUD.

### Admin impact
- Can configure many surfaces, but governance confidence is low due to inconsistent backend enforcement.

### Enterprise buyer impact
- Impressive surface breadth, but critical due-diligence concerns remain:
  - enforcement consistency
  - workflow controls
  - non-email integration maturity

---

## 15) Priority Matrix

### Critical
- Enforce RBAC permissions consistently on all organisation/settings write APIs (not just auth).
- Resolve onboarding/settings ownership overlap to remove conflicting setup paths.
- Harden member/role administration guardrails (API-level separation of duties).

### Important
- Promote team management to first-class settings workflow (not backend-only capability).
- Unify settings schema and validation strategy across frontend/backend.
- Mature non-email integration lifecycle beyond status toggles.

### Later
- Deep enterprise org modeling extensions (multi-entity governance, advanced location policy).
- More intelligence/automation layers for admin configuration quality and drift detection.

---

## Final Verdict
This module is **not shallow overall**, but significant portions are still **basic CRUD + few fields with polished UI** rather than enterprise-grade operational systems.

The strongest area is communication/email integration architecture.
The weakest area is authorization consistency and workflow cohesion between onboarding and settings.

---

## Top Findings
1. RBAC model depth is good, but org/settings API enforcement is inconsistent and sometimes only auth-gated.
2. Company setup is fragmented across onboarding wizard, company onboarding page, and settings profile.
3. Team domain exists in backend but is underexposed in core settings UX.
4. Integrations are uneven: email is production-like; broader integration hub feels partly superficial.
5. Settings page is feature-dense but monolithic, increasing admin cognitive load and governance ambiguity.

## Exact Files Reviewed
- `backend/apps/accounts/views.py`
- `backend/apps/accounts/serializers.py`
- `backend/apps/organisations/models.py`
- `backend/apps/organisations/serializers.py`
- `backend/apps/organisations/views.py`
- `backend/apps/organisations/urls.py`
- `backend/apps/rbac/models.py`
- `backend/apps/rbac/views.py`
- `backend/apps/rbac/permissions.py`
- `backend/apps/rbac/utils.py`
- `backend/apps/rbac/urls.py`
- `backend/apps/integrations/models.py`
- `backend/apps/integrations/views.py`
- `backend/apps/integrations/serializers.py`
- `backend/apps/integrations/urls.py`
- `backend/apps/communications/urls.py`
- `backend/apps/communications/permissions.py`
- `backend/apps/communications/models.py`
- `backend/apps/communications/email_accounts/views.py`
- `backend/apps/communications/email_accounts/services.py`
- `backend/apps/communications/notification_control_views.py`
- `backend/apps/communications/notification_orchestration_views.py`
- `frontend/src/pages/onboarding/OnboardingWizard.tsx`
- `frontend/src/pages/onboarding/CompanyOnboarding.tsx`
- `frontend/src/components/common/OnboardingGuard.tsx`
- `frontend/src/pages/Settings.tsx`
- `frontend/src/pages/organisation/IntegrationHub.tsx`
- `frontend/src/pages/settings/NotificationControlCenter.tsx`
- `frontend/src/pages/settings/CommunicationControlCenter.tsx`
- `frontend/src/api/organisation.ts`
- `frontend/src/api/rbac.ts`
- `frontend/src/api/integrations.ts`
- `frontend/src/api/communications.ts`
- `frontend/src/App.tsx`

## Biggest Risks
- Permission enforcement gap between RBAC intent and org/settings endpoint implementation.
- Setup fragmentation causing data drift and inconsistent admin mental model.
- Overreliance on frontend orchestration for critical admin flows.
- Integration maturity mismatch (enterprise UX promise vs partial backend depth for non-email providers).

## Must Be Fixed Before Building Further Modules
1. Backend authorization consistency for organisation/member/settings mutation endpoints.
2. Single source-of-truth setup flow (onboarding vs settings separation with explicit ownership).
3. Cohesive org admin model including teams in primary workflow, not hidden backend capability.
4. Integration governance model clarity (which providers are truly operational vs placeholder).

## Recommended Next Module to Redesign
- **Member Management + RBAC Enforcement Layer** (users, role assignment, permission enforcement across org/settings APIs).

Reason: this is the highest-risk foundation; if unresolved, every future module inherits insecure or inconsistent access control behavior.
