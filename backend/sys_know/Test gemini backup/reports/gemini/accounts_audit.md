# Module Audit: accounts

## 1. Backend Files Found

* `apps/accounts/models.py`
* `apps/accounts/serializers.py`
* `apps/accounts/views.py`
* `apps/accounts/urls.py`
* `apps/accounts/app.py`
* `apps/accounts/tests/test_onboarding.py`

## 2. Frontend Usage Found

* `../frontend/src/api/auth.ts`: Contains API calls for login, register (company/agency/candidate), send-otp, verify-otp, onboarding-complete, me, logout, refresh, change-password, forgot-password, reset-password.
* `../frontend/src/pages/`: Likely `/login`, `/register`, `/onboarding`, `/profile` pages exist (inferred from API usage and `update_frontend.py` context).

## 3. Confirmed Backend Features

* **Multi-tenant Registration**: `RegisterCompanyView` and `RegisterAgencyView` create a new `Client` (tenant) and `Organisation`.
* **Candidate Identity Deduplication**: `RegisterCandidateView` uses `identity_service` to match existing users or candidate records.
* **OTP Email Verification**: `SendOTPView` and `VerifyOTPView` handle code generation, expiry (5 min), and max attempts (5).
* **Onboarding Wizard**: `CompleteOnboardingView` saves preferences and auto-configures workspace (automation rules).
* **MFA (TOTP)**: `MFAEnableView` and `MFAVerifyView` using `pyotp`.
* **User Profiles**: `MeView` handles retrieval and partial updates of user data.
* **Role-Based Access**: Role choices defined in `CustomUser` model.

## 4. Confirmed Frontend Features

* **Authentication Flows**: Login, Logout, and Token Refresh are integrated.
* **Signup Flows**: Separate flows for Company, Agency, and Candidate.
* **Verification**: OTP-based email verification is supported in the API layer.
* **Onboarding**: Integration with onboarding completion endpoint.
* **Profile Management**: Support for retrieving and updating user profile.

## 5. Backend Without Frontend

* **MFA (TOTP)**: `mfa/enable/` and `mfa/verify/` are in backend but not found in `frontend/src/api/auth.ts`.
* **Change Password**: `change-password/` is in backend and frontend api, but might be missing a UI page.

## 6. Frontend Without Backend

* None identified. The backend covers all primary auth/profile flows requested by the frontend.

## 7. Validation / Error Handling Gaps

* **Placeholder Views**: `ForgotPasswordView` and `ResetPasswordView` return success messages but don't contain implementation logic.
* **Legacy Endpoint**: `VerifyEmailView` is a placeholder for backward compatibility.
* **OTP Bypass**: Development mode allows `123456` as a master OTP, which is fine but should be strictly guarded.

## 8. Testing Coverage Gaps

* **Tested**: Onboarding flow (`test_onboarding.py`).
* **Untested**: Registration (Company/Agency/Candidate), Login, OTP verification, MFA, Password Change, Token Refresh.
* **Priority**: Registration and Login flows should be tested as they are critical for system entry.

## 9. Schema / API Documentation Gaps

* **Missing Response Metadata**: Many views return `success_response` or `error_response` which are not fully described in `@extend_schema`.
* **Default Schema Issues**: Spectacular schema often shows "No response body" for endpoints that definitely return data (e.g., `RegisterCompanyView` returns user data and tokens).

## 10. Security / Permission Concerns

* **OTP Rate Limiting**: Max 5 attempts is good, but there's no global rate limiting (e.g., per IP) for OTP requests.
* **User Enumeration**: `SendOTPView` attempts to prevent user enumeration by returning a success message even if the email doesn't exist, which is good.
* **Auth-less VerifyOTP**: `VerifyOTPView` uses `AllowAny` and no auth classes to fix a bug where expired tokens prevented verification. This is correct but makes the OTP the sole security factor.

## 11. Stability / Architecture Concerns

* **Coupling**: `CompleteOnboardingView` is heavily coupled with `apps.automation.models` and `apps.organisations.models`.
* **Hardcoded Choices**: Roles and user types are hardcoded in multiple places (models, views, serializers).

## 12. Priority Fixes

### High
* Implement `ForgotPasswordView` and `ResetPasswordView` logic.
* Add integration tests for Registration and Login.

### Medium
* Improve `@extend_schema` documentation for all auth endpoints to include response bodies.
* Implement UI for MFA if not already present.

### Low
* Clean up legacy `VerifyEmailView`.
* Centralize role/user-type choices to avoid duplication.

## 13. Unverified Items

* MFA frontend usage (UNVERIFIED).
* Actual email delivery in production (UNVERIFIED).

## 14. Recommended Next Tests

* `test_registration_company`: Verify tenant and user creation.
* `test_registration_candidate_deduplication`: Verify linking to existing candidate record.
* `test_login_unverified_email`: Ensure login fails and sends a new OTP if email is not verified.
* `test_otp_max_attempts`: Verify OTP is invalidated after 5 failed attempts.
* `test_mfa_flow`: Verify MFA enabling and subsequent verification.
