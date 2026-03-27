# Module Audit: communications

## 1. Backend Files Found

* `apps/communications/models.py`: Core models for messages, notifications, and the enterprise email engine (accounts, templates, messages).
* `apps/communications/serializers.py`: Serializers for legacy and enterprise communication models.
* `apps/communications/views.py`: Legacy views for messaging and notifications; enterprise views are split into sub-modules.
* `apps/communications/urls.py`: Unified URL patterns for the entire communication stack.
* `apps/communications/services.py`: `EmailRoutingService` facade for backward-compatible email dispatch.
* `apps/communications/feature_readiness.py`: Dynamic checks for system readiness (database, OAuth settings).
* Sub-modules: `email_accounts/`, `email_dispatch/`, `email_templates/`, `email_audit/`, `email_webhooks/`.

## 2. Frontend Usage Found

* `../frontend/src/api/communications.ts`: Comprehensive integration for email account management, template editing, and notification tracking.
* `../frontend/src/api/communications.ts` calls several OAuth and SMTP configuration endpoints.

## 3. Confirmed Backend Features

* **Enterprise Communication Engine**: Support for multiple email providers (Gmail OAuth, Microsoft OAuth, SMTP) with unified dispatching and tracking.
* **Unified Email Routing**: `EmailRoutingService` handles legacy calls by routing them through the new enterprise engine.
* **Dynamic Template System**: Support for system-default and tenant-custom templates with versioning and variable schemas.
* **In-App Notifications**: `Notification` model tracks system alerts for users with `is_read` and `action_url`.
* **Credential Security**: SMTP passwords and OAuth tokens are stored in encrypted format (`smtp_password_encrypted`, `access_token_encrypted`).
* **Variable Rendering**: Backend supports rendering templates and quick-replies with dynamic context.

## 4. Confirmed Frontend Features

* **Email Connection Wizard**: Connecting and testing Gmail, Microsoft, and SMTP accounts.
* **Notification Feed**: Real-time (inferred) alert system with mark-as-read functionality.
* **Template Editor**: CRUD operations for email templates and quick replies.
* **Email Preview**: Live rendering of templates before sending.

## 5. Backend Without Frontend

* **Email Delivery Webhooks**: Comprehensive support for handling provider events (delivered, bounced, opened, clicked) in `email_webhooks/`, but no integrated UI for recruiters to see detailed delivery status yet.
* **Microsoft OAuth Support**: Initiate and callback views exist, though Gmail appears to be the primary focus in the current frontend API calls.

## 6. Frontend Without Backend

* None identified. The backend provides a very sophisticated API for all frontend communication features.

## 7. Validation / Error Handling Gaps

* **Silent Failures in Facade**: `EmailRoutingService` catches all exceptions and simply returns `False`, making it difficult to debug failures in legacy email calls.
* **Manual Schema Verification**: `feature_readiness.py` is used as a runtime check for database tables instead of relying on standard Django system checks.
* **Incomplete Error Feedback**: OAuth callback views may fail silently or return generic error responses if provider tokens are invalid.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/communications/`. This is a major gap for a core business feature.
* **Priority**: Integration tests for the OAuth connection flow and the template rendering/dispatch engine.

## 9. Schema / API Documentation Gaps

* **Missing Detailed Schemas**: Many views lack `@extend_schema` to describe their complex response payloads (e.g., the mixed OAuth/Status payloads).
* **Undocumented Response Fields**: The health status and failure reasons for email accounts are not explicitly defined in the OpenAPI schema.

## 10. Security / Permission Concerns

* **Insufficient Account Permissions**: `EmailAccountViewSet` only checks for personal ownership. The `EmailAccountPermission` model exists but is not yet fully integrated into the API layer to support `TENANT_SHARED` accounts.
* **Encryption Key Management**: Credentials are encrypted using a system-level key. If this key is compromised, all SMTP passwords and OAuth tokens are exposed.

## 11. Stability / Architecture Concerns

* **Fragmented Model Layers**: The module has both "Legacy" models and "Enterprise" models which can lead to confusion and data duplication during the transition period.
* **Implicit Coupling**: The `EmailRoutingService` is called by nearly every other module (Accounts, Jobs, Agencies, Pipeline) without a clear dependency management strategy.

## 12. Priority Fixes

### High
* **Implement Tests**: Add comprehensive test suite for email dispatch and template rendering.
* **Standardize Error Handling**: Improve `EmailRoutingService` to return detailed error messages or raise specific exceptions.

### Medium
* **Complete RBAC Integration**: Integrate the `EmailAccountPermission` model into the API layer to support shared email accounts.
* **Enhance OpenAPI Documentation**: Add detailed schemas for all communication-related endpoints.

### Low
* **Cleanup Legacy Models**: Begin the migration process to move all communication data to the new Enterprise models and deprecate the legacy ones.

## 13. Unverified Items

* WhatsApp and SMS integration (UNVERIFIED — mentioned in `message_type` choices but no dedicated views seen).
* Real-time notification delivery via WebSockets (UNVERIFIED).

## 14. Recommended Next Tests

* `test_email_oauth_initiate_gmail`: Verify the generation of a valid Google OAuth authorization URL.
* `test_template_render_with_context`: Verify that `variables_schema_json` correctly populates data into a rendered email.
* `test_email_dispatch_retry_logic`: Verify that the system attempts to retry or logs an error for failed SMTP deliveries.
* `test_notification_read_all`: Verify that the mark-all-as-read endpoint correctly updates unread notification counts.
* `test_account_health_check`: Verify that the `/test` endpoint correctly identifies unhealthy SMTP connections.
