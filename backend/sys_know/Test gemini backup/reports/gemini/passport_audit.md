# Module Audit: passport

## 1. Backend Files Found

* `apps/passport/models.py`: Defines `TalentPassport`, `ResumeVersion`, `PassportAccessLog`, `PassportRevocation`, and `DataWithdrawalRequest`.
* `apps/passport/serializers.py`: Serializers for full passport, public view, resume versions, and access logs.
* `apps/passport/views.py`: Main views for profile management, sharing, and importing.
* `apps/passport/urls.py`: URL patterns for candidate and public passport access.
* `apps/passport/candidate_sync_views.py`: Logic for linking users to candidate records and prefilling onboarding.
* `apps/passport/withdrawal_views.py`: Implementation of GDPR-compliant data withdrawal and anonymization.

## 2. Frontend Usage Found

* `../frontend/src/api/passport.ts`: Extensive integration for managing the talent passport, generating share links, and importing candidates.
* `../frontend/src/api/passport.ts` uses `/passport/my-candidate/` for onboarding prefill.

## 3. Confirmed Backend Features

* **Non-Destructive Data Merging**: `_merge_passport_data` uses union-merge for list fields and protects existing text fields from being overwritten by blank submissions.
* **Granular Privacy & Sharing**: Support for unique magic-link share tokens that can be regenerated or revoked per-tenant.
* **Audit Trail (GDPR-compliant)**: `PassportAccessLog` tracks every view or import of a passport, including IP address and accessing user/tenant.
* **Automated Data Anonymization**: `DataWithdrawalView` immediately strips PII and schedules full deletion after a 30-day "cool-off" period.
* **Identity Linkage Engine**: `_find_linked_candidate` uses multi-level matching (user_id -> email -> phone) to connect new users to existing recruiter-added candidate records.
* **Profile Scoring**: Integrated calculation of profile completeness to encourage candidate engagement.

## 4. Confirmed Frontend Features

* **Onboarding Wizard Prefill**: Automatically populating registration forms with data from existing candidate profiles.
* **Talent Profile Dashboard**: Comprehensive editing of professional details, CVs, and social links.
* **Recruiter Import Flow**: Seamlessly adding candidates to the CRM pool via their shared talent passport link.
* **Share Link Management**: UI for generating and resetting public profile access.

## 5. Backend Without Frontend

* **Resume Versioning System**: Backend tracks multiple versions of uploaded resumes via `ResumeVersion`, which may not be fully utilized in the current UI.
* **Granular Access Revocation**: Detailed backend support for revoking access from specific tenants (`MyPassportRevokeAccessView`) may lack a dedicated management UI for candidates.

## 6. Frontend Without Backend

* None identified. The backend provides a solid foundation for all candidate profile and privacy features.

## 7. Validation / Error Handling Gaps

* **Anonymization Scope**: `DataWithdrawalView` currently misses anonymizing several PII-heavy fields like `skills`, `languages`, and `education` during the initial phase.
* **Import Side-Effects**: `PassportImportView` creates candidates manually; it should ideally use a factory or service to ensure consistent model creation across the system.
* **Incomplete Validation**: `MyPassportView.put` performs manual merging before the serializer, which might bypass some field-level validation rules during the merge step.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/passport/`. This is a significant risk given the privacy-centric nature of the data.
* **Priority**: Integration tests for the privacy revocation logic and the identity matching engine.

## 9. Schema / API Documentation Gaps

* **Nested JSON Definitions**: The OpenAPI schema does not define the internal structure of `work_history`, `education`, or `skills` JSON fields.
* **Public Token Description**: The public view endpoint lacks detailed documentation on how the token behaves or its expiration logic.

## 10. Security / Permission Concerns

* **Token-based Public Access**: The `PublicPassportView` is `AllowAny`. Rate-limiting is essential to prevent systematic harvesting of candidate profiles via token brute-forcing.
* **PII Redaction**: `TalentPassportPublicSerializer` correctly limits fields, but should also ensure that any PII hidden by user visibility settings is strictly redacted.

## 11. Stability / Architecture Concerns

* **Side-Effect Onboarding**: `MyPassportView.put` automatically creates a new passport record if one doesn't exist. This is a convenient but implicit side-effect.
* **Logic Duplication**: Some fields (e.g., `experience_years`) are duplicated between the `Candidate` and `TalentPassport` models, requiring careful synchronization.

## 12. Priority Fixes

### High
* **Implement Tests**: Add comprehensive test suite for identity matching and privacy revocation.
* **Expand Anonymization**: Update `DataWithdrawalView` to immediately strip all PII fields (Work History, Education, Certifications) upon request.

### Medium
* **Refactor Import Logic**: Move the candidate creation logic from `PassportImportView` to a centralized Candidate Service.
* **Enhance OpenAPI Documentation**: Add detailed schemas for nested profile JSON fields.

### Low
* **Sync Strategy**: Implement a clear strategy or signals for keeping `TalentPassport` and linked `Candidate` records synchronized.

## 13. Unverified Items

* Background and identity verification third-party integrations (UNVERIFIED — fields exist but no logic seen).
* Automated resume parsing logic for imported CVs (UNVERIFIED).

## 14. Recommended Next Tests

* `test_passport_data_merge_union`: Verify that updating skills in the passport appends new skills without erasing existing ones.
* `test_identity_match_email_priority`: Verify that `_find_linked_candidate` correctly prioritizes user_id match over email match.
* `test_public_access_logging`: Verify that every view of a public passport link generates a corresponding `PassportAccessLog` entry.
* `test_privacy_revocation_enforcement`: Verify that after access is revoked from a tenant, that tenant can no longer view the public passport.
* `test_data_withdrawal_anonymization`: Verify that initiating withdrawal immediately renders the profile invisible and strips key PII fields.
