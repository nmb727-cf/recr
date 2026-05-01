# Authentication & Roles Module Verification Report

**Status:** Phase 1 Audit
**Date:** 2026-04-07
**Author:** Senior System Architect & QA Auditor

## 1. Implemented Features

### Backend
- **Single login for all user types**: `LoginView` in `accounts/views.py` supports unified authentication for Company, Agency, and Candidate users using Django's `authenticate` and JWT tokens.
- **Company registration**: `RegisterCompanyView` correctly creates a tenant (Client), a `tenant_admin` user, and an `Organisation` record.
- **Agency registration**: `RegisterAgencyView` correctly creates a tenant (Client), an `agency_owner` user, and an `Organisation` record.
- **Candidate registration**: `RegisterCandidateView` handles initial user creation with identity deduplication (matching by email/phone). Candidates are assigned to the `public` tenant.
- **Email verification (OTP)**: Implemented via `EmailOTP` model and `VerifyOTPView`. Includes a development mode bypass ('123456').
- **Role-based access control (RBAC)**: Robust permission-based role system implemented in `apps/rbac`. Role names mirror `CustomUser.role`.
- **Permission middleware**: `require_permission` factory in `apps/rbac/permissions.py` is widely used across all functional modules (interviews, communications, etc.).
- **Department & Branch management**: Fully implemented in `organisations/views.py` with `Department` and `Location` models.
- **Tenant isolation**: Data is partitioned by `tenant_id` at the database level. Views manually enforce filtering by `request.user.tenant_id`.
- **Data Privacy**: Isolation of private data (like `CandidateNote`) between Company and Agency is enforced by strict `tenant_id` filtering, even when viewing the same candidate.
- **Candidate Global Entity**: Implemented via a shared `Candidate` record linked across tenants using a `global_hash` and `user_id`. Tenant-specific data is stored in `CandidateWorkspace`.

### Frontend
- **Login UI**: Unified `Login.tsx` supports all user roles.
- **Registration UI**: Separate flows for `RegisterCompany`, `RegisterAgency`, and `RegisterCandidate`.
- **Department/Branch UI**: Implemented within the Settings page (`DepartmentsTab`, `LocationsTab`).

---

## 2. Partially Implemented

- **Multi-user invite system**:
    - **Backend**: `UserListView.post` creates the user and assigns the role, but has a `# TODO: Send invite email with temp password`. Currently, no email is sent to the invited user.
    - **Security**: Invites use a `temp_password` instead of a token-based verification/onboarding link.
- **Candidate registration workflow**:
    - The `Candidate` record is not created immediately upon signup. It is lazily created during the "Passport" (profile) save step (`MyPassportView.put`). A candidate who signs up but never completes their profile will have a `CustomUser` record but no `Candidate` record.
- **Agency role UI**: The `UsersTab` in `Settings.tsx` has hardcoded Company roles (`hr_manager`, `recruiter`, etc.) in the invite select menu. Agency roles (`agency_admin`, `agency_recruiter`) are missing from the UI.

---

## 3. Missing

- **Agency Sourcer Role**: The `agency_sourcer` role is missing from both the `CustomUser` model choices and the `rbac` permission registry.
- **Department management in invite**: The invite system does not yet allow assigning a user to a specific department or branch during invitation (though they can be edited later).

---

## 4. Logic Issues

- **Manual Tenant Filtering**: Multi-tenancy is enforced manually in every view (e.g., `.filter(tenant_id=request.user.tenant_id)`). This is a maintenance risk; a missing filter could lead to cross-tenant data leaks. An automated mechanism (like a custom manager or Global Query Filter) would be more robust.
- **Registration Deduplication**: While `RegisterCandidateView` has identity deduplication, `RegisterCompanyView` and `RegisterAgencyView` only check for existing emails. They do not handle cases where a user might already have an account (e.g., as a candidate) and wants to register a company.

---

## 5. Architecture Issues

- **Role Choice Coupling**: Role names are duplicated between `CustomUser.role` choices and the `rbac.Role` model. The system relies on string matching between these, which could break if not kept in sync via `seed_rbac`.
- **Candidate "Global" Isolation**: Placing all candidates in the `public` tenant is functional but requires absolute diligence in `apps/candidates/views.py` to ensure candidates cannot see each other's data (currently filtered by `user_id`).

---

## Summary Table

| Requirement | Status | Note |
|-------------|--------|------|
| Single login | ✅ | Functional |
| Company registration | ✅ | Functional |
| Agency registration | ✅ | Functional |
| Candidate registration | ⚠️ | Lazy creation of Candidate record |
| Email verification | ✅ | OTP-based |
| RBAC | ✅ | Permission-based |
| Multi-user invite | ⚠️ | No email sent, missing Agency roles in UI |
| Department management | ✅ | Functional |
| Branch management | ✅ | Functional |
| Permission-based roles | ✅ | Wide usage of require_permission |
| Company/Agency isolation| ✅ | Enforced via tenant_id on entities |
| Candidate global entity | ✅ | Linked via user_id/global_hash |

**Recommendation:**
1. Implement the invitation email sending logic.
2. Add `agency_sourcer` role to backend and frontend.
3. Update `UsersTab` to dynamically show roles based on the organisation type.
4. Consider a base model or manager to automate `tenant_id` filtering.
