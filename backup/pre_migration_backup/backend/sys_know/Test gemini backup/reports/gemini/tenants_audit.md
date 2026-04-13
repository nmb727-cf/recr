# Module Audit: tenants

## 1. Backend Files Found

* `apps/tenants/models.py`: Defines the `Client` (tenant) and `Domain` models.
* `apps/tenants/apps.py`: App configuration.
* `apps/tenants/migrations/`: Initial multi-tenancy schema setup.

## 2. Frontend Usage Found

* **INDIRECT**: No dedicated `tenants.ts` API file was found. Tenant information (slug, name, type) is typically delivered to the frontend as part of the `LoginResponse` or `MeView` response in the `accounts` module.

## 3. Confirmed Backend Features

* **Schema-based Multi-Tenancy**: Built on `django-tenants`, utilizing PostgreSQL schemas for strict data isolation between clients.
* **Automated Provisioning**: `auto_create_schema = True` ensures that a new database schema is automatically created when a `Client` record is saved.
* **Tenant Categorization**: Support for multiple tenant types: `Company`, `Agency`, and `Candidate Pool`.
* **Domain Routing**: The `Domain` model allows routing requests to the correct tenant schema based on the request hostname.
* **Lifecycle Tracking**: Support for tenant statuses (`Pending`, `Active`, `Suspended`, `Terminated`).

## 4. Confirmed Frontend Features

* **NONE**: No standalone frontend features for tenant management were identified in the source code.

## 5. Backend Without Frontend

* **Everything**: The tenant management layer (creation, suspension, domain assignment) exists in the backend but lacks a public-facing management API or UI.

## 6. Frontend Without Backend

* None identified.

## 7. Validation / Error Handling Gaps

* **Incomplete CRUD**: The module only contains models. All tenant creation logic is currently nested within the `accounts` registration views, making it difficult to manage tenants independently.
* **Manual Cleanup**: There is no evidence of automated schema deletion or archiving logic when a tenant is marked as `is_deleted` or `Terminated`.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found for the multi-tenancy layer. This is the most critical architectural component of the platform.
* **Priority**: Integration tests for cross-tenant data isolation and automated schema creation.

## 9. Schema / API Documentation Gaps

* **No Public API**: As there are no views or serializers currently defined in the `tenants` app, there is no corresponding OpenAPI documentation.

## 10. Security / Permission Concerns

* **Cross-Tenant Leaks**: The entire security model of the SaaS depends on the correctness of the schema-switching logic. Any failure in the `django-tenants` middleware could lead to catastrophic data leaks between clients.
* **Master Tenant Access**: The `is_master` flag suggests a "god tenant" concept which needs extremely strict access controls.

## 11. Stability / Architecture Concerns

* **Coupling with Accounts**: Tenant creation is tightly coupled with user registration in `apps.accounts.views`. A more modular approach would involve a dedicated Tenant Service.
* **Migration Complexity**: Running migrations across hundreds of tenant schemas can be slow and error-prone without robust automation.

## 12. Priority Fixes

### High
* **Implement Isolation Tests**: Add rigorous tests to verify that data from one tenant schema is never accessible from another.
* **Implement Management API**: Create a dedicated administrative API for managing tenant lifecycles (Suspend/Reactivate/Terminate).

### Medium
* **Enhance Cleanup Logic**: Implement background tasks to safely archive and eventually purge data for terminated tenants.

### Low
* **Standardize Metadata**: Ensure all tenant-level settings are consistently stored in either `Client` metadata or the `Organisation` model to avoid confusion.

## 13. Unverified Items

* Performance of schema-switching at scale (UNVERIFIED).
* Robustness of the shared-schema (`public`) vs. tenant-schema data split (UNVERIFIED).

## 14. Recommended Next Tests

* `test_tenant_schema_creation`: Verify that creating a `Client` record correctly triggers the creation of a new PostgreSQL schema.
* `test_data_isolation_check`: Verify that a query executed in Tenant A's context returns zero results from Tenant B's tables.
* `test_domain_routing_logic`: Verify that different hostnames correctly route to their respective tenant schemas.
* `test_tenant_suspension_blocking`: Verify that users of a `Suspended` tenant are blocked from accessing any API endpoints.
* `test_public_schema_access`: Verify that shared tables (e.g., `tenants_client`) are accessible from the `public` schema.
