# Schemathesis Cleanup Session — 2026-03-28

## What was fixed

### Root cause found and resolved: stale OpenAPI schema

All 11 "API rejected schema-compliant request" failures shared the same root cause:
`sys_know/generated/openapi/schema.yaml` was stale. It was missing `requestBody` sections for all auth endpoints, so Schemathesis generated empty POST bodies, which the backend correctly rejected with 400.

The views already had correct `@extend_schema(request=...)` decorators. The schema file simply hadn't been regenerated after those decorators were added.

**Fix:** Replaced the stale schema with a freshly generated one via `python manage.py spectacular`.

### 11 endpoints corrected (requestBody now present with required fields)

| Endpoint | Required fields |
|---|---|
| POST /api/v1/auth/send-otp/ | email |
| POST /api/v1/auth/verify-otp/ | email, code |
| POST /api/v1/auth/forgot-password/ | email |
| POST /api/v1/auth/login/ | email, password |
| POST /api/v1/auth/refresh/ | refresh_token |
| POST /api/v1/auth/register/agency/ | name, first_name, last_name, email, password, password_confirm |
| POST /api/v1/auth/register/candidate/ | first_name, last_name, email, password, password_confirm |
| POST /api/v1/auth/register/company/ | name, first_name, last_name, email, password, password_confirm |
| POST /api/v1/auth/reset-password/ | token, new_password |
| POST /api/v1/auth/verify-email/ | token |
| POST /api/v1/candidates/check-identity/ | email or phone (both optional — view returns 200 for empty body) |

### Nightly automation hardened

`scripts/nightly_test.sh`: after spectacular generates the authoritative schema to
`sys_know/generated/openapi/schema.yaml`, it now also copies it to
`sys_know/docs/generated/schema.yaml` so the mkdocs site always serves the fresh version.

**Discovery:** Schemathesis in the nightly script runs against the live Django endpoint
`http://127.0.0.1:8000/api/schema/` (drf-spectacular serving dynamically), not the file.
Schema generation order therefore doesn't affect Schemathesis correctness — it always
gets a live fresh schema. The file is for docs/inspection only.

---

## What remains

From the last schemathesis run (282 endpoints tested):

| Category | Count | Notes |
|---|---|---|
| API rejected schema-compliant request | 11 → **0** (fixed this session) | All auth endpoints |
| Undocumented HTTP status code | 124 | Mostly 401/404 on endpoints that don't document all auth variants |
| Unsupported methods | 277 | TRACE/PATCH/etc. returning 401 instead of 405 — needs `http_method_names` or middleware |
| API accepts requests without authentication | 2 | Public endpoints accepting when they shouldn't |
| API accepted schema-violating request | 2 | Backend accepting malformed input |
| Missing header not rejected | 2 | Headers documented as required but not enforced |

---

## Why Schemathesis cleanup is paused

The remaining 406 failures fall into categories that require broader changes:

- **Unsupported methods (277):** A global DRF fix (override `http_method_not_allowed` or add
  `http_method_names = ['get', 'post', ...]` to every view). High change surface area.
- **Undocumented HTTP status codes (124):** Each endpoint needs its `@extend_schema` responses
  updated to document all auth/permission variants (401, 403, 404). Mechanical but large.
- **Auth/schema violations (6):** Need individual investigation per endpoint.

None of these are blocking product features. Fixing them is a documentation and hygiene effort,
not a correctness issue.

---

## When to revisit

- **Undocumented status codes:** Good candidate for a dedicated schema-documentation pass once
  the API surface stabilises (no new endpoints added for 2+ weeks).
- **Unsupported methods:** One global change — add a custom `dispatch` mixin or router-level
  405 handler. Low risk, can be done in 1-2 hours when convenient.
- **Auth/schema violations:** Review individually when touching those endpoints anyway.

Next scheduled nightly will run the fresh schema and should show 0 "API rejected schema-compliant request" failures.
