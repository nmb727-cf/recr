# Nightly Summary

## pytest
```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
django: version: 6.0.3, settings: config.settings.base (from ini)
rootdir: /home/nirav/projects/SaaS_Project
configfile: pytest.ini
testpaths: backend
plugins: schemathesis-4.14.0, django-4.12.0, base-url-2.1.0, hypothesis-6.151.9, playwright-0.7.2, anyio-4.13.0, cov-7.1.0
collected 3 items

backend/apps/accounts/tests/test_onboarding.py ...                       [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________

Coverage HTML written to dir /home/nirav/projects/SaaS_Project/sys_know/generated/coverage/htmlcov
Coverage XML written to file /home/nirav/projects/SaaS_Project/sys_know/generated/coverage/coverage.xml
============================== 3 passed in 4.72s ===============================
```
## schema
```
Warning: operationId "v1_jobs_requisitions_retrieve" has collisions [('/api/v1/jobs/requisitions/', 'get'), ('/api/v1/jobs/requisitions/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_jobs_postings_retrieve" has collisions [('/api/v1/jobs/postings/', 'get'), ('/api/v1/jobs/postings/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_candidates_retrieve" has collisions [('/api/v1/candidates/', 'get'), ('/api/v1/candidates/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_candidates_engagements_retrieve" has collisions [('/api/v1/candidates/{candidate_id}/engagements/', 'get'), ('/api/v1/candidates/{candidate_id}/engagements/{engagement_id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_applications_retrieve" has collisions [('/api/v1/applications/', 'get'), ('/api/v1/applications/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_agencies_relationships_retrieve" has collisions [('/api/v1/agencies/relationships/', 'get'), ('/api/v1/agencies/relationships/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_agencies_assignments_retrieve" has collisions [('/api/v1/agencies/assignments/', 'get'), ('/api/v1/agencies/assignments/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_interviews_templates_retrieve" has collisions [('/api/v1/interviews/templates/', 'get'), ('/api/v1/interviews/templates/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_interviews_retrieve" has collisions [('/api/v1/interviews/', 'get'), ('/api/v1/interviews/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_messages_threads_retrieve" has collisions [('/api/v1/messages/threads/', 'get'), ('/api/v1/messages/threads/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_communication_templates_retrieve" has collisions [('/api/v1/communication/templates/', 'get'), ('/api/v1/communication/templates/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_communications_email_messages_retrieve" has collisions [('/api/v1/communications/email-messages/', 'get'), ('/api/v1/communications/email-messages/{id}', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_documents_retrieve" has collisions [('/api/v1/documents/', 'get'), ('/api/v1/documents/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_offers_retrieve" has collisions [('/api/v1/offers/', 'get'), ('/api/v1/offers/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_candidate_applications_retrieve" has collisions [('/api/v1/candidate/applications/', 'get'), ('/api/v1/candidate/applications/{id}/', 'get')]. resolving with numeral suffixes.

Schema generation summary:
Warnings: 19 (19 unique)
Errors:   942 (188 unique)

```
## schemathesis
```
  ❌ API accepts requests without authentication: 2
  ❌ API accepted schema-violating request: 2
  ❌ API rejected schema-compliant request: 11
  ❌ Missing header not rejected: 2
  ❌ Undocumented HTTP status code: 124
  ❌ Unsupported methods: 277

Errors:
  🚫 Network Error: 8

Warnings:
  ⚠️ Missing authentication: 279 operations returned only 401/403 responses
  ⚠️ Missing valid test data: 11 operations repeatedly returned 404 responses

Test cases:
  15789 generated, 414 found 418 unique failures, 175 skipped

Seed: 320429938304571368857130907205107386654

================ 418 failures, 8 errors, 2 warnings in 1135.98s ================
```
## vitest
```

> frontend@0.0.0 test
> vitest --run


[31m⎯⎯⎯⎯⎯⎯⎯[39m[1m[41m Startup Error [49m[22m[31m⎯⎯⎯⎯⎯⎯⎯⎯[39m
file:///home/nirav/projects/SaaS_Project/frontend/node_modules/rolldown/dist/shared/rolldown-build-CPrIX9V6.mjs:9
import { formatWithOptions, styleText } from "node:util";
                            ^^^^^^^^^
SyntaxError: The requested module 'node:util' does not provide an export named 'styleText'
    at ModuleJob._instantiate (node:internal/modules/esm/module_job:123:21)
    at async ModuleJob.run (node:internal/modules/esm/module_job:191:5)
    at async ModuleLoader.import (node:internal/modules/esm/loader:336:24)
    at async start (file:///home/nirav/projects/SaaS_Project/frontend/node_modules/vitest/dist/chunks/cac.DRKYQDPl.js:2327:27)



```
## playwright
```

Running 1 test using 1 worker

[1A[2K[1/1] tests/smoke.spec.ts:3:1 › app loads
[1A[2K  1 passed (1.6s)
```
## mkdocs
```
[31m │[0m
[31m │  × [0mAll plugins will stop working – the plugin system has been removed
[31m │  × [0mAll theme overrides will break – the theming system has been rewritten
[31m │  × [0mNo migration path exists – existing projects cannot be upgraded
[31m │  × [0mClosed contribution model – community members can't report bugs
[31m │  × [0mCurrently unlicensed – unsuitable for production use
[31m │[0m
[31m │[0m  Our full analysis:
[31m │[0m
[31m │[0m  [4mhttps://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/[0m
[0m
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: /home/nirav/projects/SaaS_Project/sys_know/site
INFO    -  The following pages exist in the docs directory, but are not included in the "nav" configuration:
  - Testing_And_Documentation_Guide.md
  - reports/backend_frontend_gap.md
  - reports/nightly_summary.md
WARNING -  Doc file 'dashboard/index.md' contains a link '../generated/coverage/htmlcov/index.html', but the target 'generated/coverage/htmlcov/index.html' is not found among documentation files.
WARNING -  Doc file 'dashboard/index.md' contains a link '../generated/openapi/schema.yaml', but the target 'generated/openapi/schema.yaml' is not found among documentation files.
INFO    -  Documentation built in 0.14 seconds
```
