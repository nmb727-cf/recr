# PLATFORM CORE EXTRACTION TODO

During extraction, preserve all currently working company, agency, and candidate behavior; split mixed files without dropping supported paths.

1.  **Move tenant/context helpers**
    *   Backend: `backend/shared/tenant_access.py` -> `apps/platform_core/tenants/`
    *   Frontend: Tenant context/hooks -> `platform_core/tenants/`
    *   *Note: Preserve Company/Agency role sets during move.*

2.  **Move auth/session helpers**
    *   Backend: `apps/core/authentication.py` -> `apps/platform_core/auth/`
    *   Frontend: `utils/authSession.ts`, `utils/authAccess.ts` -> `platform_core/auth/`
    *   *Note: Preserve all actor login/session paths.*

3.  **Move permission utilities**
    *   Backend: `apps/rbac/utils.py` -> `apps/platform_core/rbac/`
    *   Frontend: `utils/permissions.ts`, `hooks/usePermission.ts` -> `platform_core/rbac/`
    *   *Note: Keep all existing permission codes intact.*

4.  **Move notifications infrastructure**
    *   Backend: Core delivery models -> `apps/platform_core/notifications/`
    *   Frontend: Notification API and shell components -> `platform_core/notifications/`
    *   *Note: Ensure both agency and company alerts remain functional.*

5.  **Move security/audit/event helpers**
    *   Backend: Middleware and core events -> `apps/platform_core/security/` and `apps/platform_core/events/`
    *   *Note: Preserve request isolation logic for different actors.*

6.  **Move global config and translation helpers**
    *   Backend: `apps/translations/` logic -> `apps/platform_core/i18n/`
    *   Frontend: `i18n/` content -> `platform_core/i18n/`
    *   *Note: Preserve all existing localized strings for all actors.*
