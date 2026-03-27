# Module Audit: translations

## 1. Backend Files Found

* `apps/translations/models.py`: Defines `TranslationOverride` (for UI labels) and `ContentTranslation` (for user-generated text).
* `apps/translations/views.py`: Contains `TranslationOverrideListView` for public fetching of overrides.
* `apps/translations/urls.py`: Maps the `/overrides/` endpoint.
* `apps/translations/admin.py`: Explicit registration of models for management via Django Admin.

## 2. Frontend Usage Found

* **INFERRED**: The frontend likely calls `/api/v1/translations/overrides/` during its bootstrap process to fetch DB-backed label overrides and merge them with static local JSON translation files. No dedicated API file was found in `../frontend/src/api/`, suggesting this is handled by a core utility or bootstrap script.

## 3. Confirmed Backend Features

* **Dynamic UI Label Overrides**: Support for changing frontend labels (e.g., "Candidate" to "Applicant") without a code deploy.
* **Hierarchical Resolution**: Support for a three-layer translation hierarchy: Tenant Override > Global Override > Static JSON File.
* **Non-Destructive Content Translation**: The `ContentTranslation` model ensures original user content is never modified, storing only additional translated copies.
* **Multi-Source Support**: Tracking whether a translation was provided by a user, a machine, or reviewed by a human.
* **Public Accessibility**: The override endpoint is accessible without authentication to allow the UI to localize its login and signup screens.

## 4. Confirmed Frontend Features

* **NONE**: No explicit frontend features were identified in the source code, although the backend architecture strongly supports a flexible i18n implementation.

## 5. Backend Without Frontend

* **Content Translation Management**: While the `ContentTranslation` model is well-defined, there are currently no views or API endpoints to manage or retrieve translations for user-generated content (e.g., job descriptions or candidate notes).
* **Tenant Self-Service**: There is no API for tenants to manage their own translation overrides; this currently requires Django Admin access.

## 6. Frontend Without Backend

* None identified.

## 7. Validation / Error Handling Gaps

* **Silent Missing Keys**: If a frontend key is missing from the DB, the system returns an empty dictionary without indicating that the key is unregistered.
* **Language Code Validation**: The API does not validate if the requested `lang` code is part of the system's supported languages.
* **Conflict Resolution**: `unique_together` on the model handles DB-level conflicts, but the API doesn't provide user-friendly error messages if a tenant tries to create a duplicate override.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/translations/`.
* **Priority**: Integration tests for the hierarchical override resolution logic (ensuring tenant wins over global).

## 9. Schema / API Documentation Gaps

* **Generic Overrides Object**: The response shape for `overrides` (a flat key-value dictionary) is not explicitly defined in the OpenAPI schema.
* **Undocumented Parameters**: The `module` and `tenant` query parameters are not documented in the generated API schema.

## 10. Security / Permission Concerns

* **Public Label Exposure**: The `AllowAny` permission on `overrides/` means any actor can fetch all global and tenant-specific UI label overrides. While usually harmless, if sensitive tenant-specific terminology is used, it could represent a minor information leak.
* **Tenant Enumeration**: A malicious actor could potentially probe for valid `tenant_id` values by checking which ones return non-empty overrides.

## 11. Stability / Architecture Concerns

* **Bootstrap Dependency**: The application UI is heavily dependent on this endpoint during startup. High latency or downtime here will delay the rendering of the entire application.
* **Dictionary Growth**: If thousands of overrides are created, the response size for `overrides/` could grow significantly, affecting load times.

## 12. Priority Fixes

### High
* **Implement Tests**: Add core tests for override resolution and hierarchy.
* **Restrict Public Access**: Consider signing the `tenant_id` in the override request or requiring a valid tenant slug to minimize probing risks.

### Medium
* **Expose Management API**: Add CRUD views for `TranslationOverride` and `ContentTranslation` to allow in-app management.
* **Enhance OpenAPI Documentation**: Add detailed schemas for the translation override payload.

### Low
* **Implement Caching**: Add a caching layer to `TranslationOverrideListView` to minimize DB lookups on every app reload.

## 13. Unverified Items

* Integration with third-party translation services (Google Translate, DeepL) (UNVERIFIED — mentioned in `TRANSLATION_SOURCE_CHOICES` but no logic seen).
* Language detection logic for user-generated content (UNVERIFIED).

## 14. Recommended Next Tests

* `test_override_hierarchy_resolution`: Verify that tenant-specific values correctly overwrite global values for the same key.
* `test_override_module_filtering`: Verify that the `module` query parameter correctly filters the returned overrides.
* `test_public_access_no_auth`: Verify that the endpoint returns 200 OK for unauthenticated requests.
* `test_content_translation_persistence`: Verify that a `ContentTranslation` record can be created without modifying the source entity.
* `test_unsupported_language_fallback`: Verify the system's behavior when an unsupported or invalid language code is requested.
