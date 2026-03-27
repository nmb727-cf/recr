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
============================== 3 passed in 4.63s ===============================
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
Errors:   1029 (190 unique)

```
## schemathesis
```
Usage: schemathesis run [OPTIONS] LOCATION
Try 'schemathesis run -h' for help.

Error: Invalid value for '--report': invalid choice(s): html. Choose from junit, vcr, har, ndjson, allure.
```
## vitest
```
  when one of the dependencies in your package.json depends on @playwright/test.[39m
[90m [2m❯[22m TestTypeImpl._currentSuite node_modules/playwright/lib/common/testType.js:[2m75:13[22m[39m
[90m [2m❯[22m TestTypeImpl._createTest node_modules/playwright/lib/common/testType.js:[2m88:24[22m[39m
[90m [2m❯[22m node_modules/playwright/lib/transform/transform.js:[2m282:12[22m[39m
[36m [2m❯[22m tests/smoke.spec.ts:[2m3:1[22m[39m
    [90m  1|[39m [35mimport[39m { test[33m,[39m expect } [35mfrom[39m [32m'@playwright/test'[39m
    [90m  2|[39m
    [90m  3|[39m [34mtest[39m([32m'app loads'[39m[33m,[39m [35masync[39m ({ page }) [33m=>[39m {
    [90m   |[39m [31m^[39m
    [90m  4|[39m   [35mawait[39m page[33m.[39m[34mgoto[39m([32m'/'[39m)
    [90m  5|[39m   [35mawait[39m [34mexpect[39m(page)[33m.[39m[34mtoHaveURL[39m([36m/.*/[39m)

[31m[2m⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/1]⎯[22m[39m


[2m Test Files [22m [1m[31m1 failed[39m[22m[2m | [22m[1m[32m1 passed[39m[22m[90m (2)[39m
[2m      Tests [22m [1m[32m1 passed[39m[22m[90m (1)[39m
[2m   Start at [22m 17:20:04
[2m   Duration [22m 1.09s[2m (transform 29ms, setup 80ms, import 13ms, tests 2ms, environment 677ms)[22m

```
## playwright
```

Running 1 test using 1 worker

[1A[2K[1/1] tests/smoke.spec.ts:3:1 › app loads
[1A[2K  1 passed (1.5s)

To open last HTML report run:
[36m[39m
[36m  npx playwright show-report ../sys_know/generated/test-results/playwright-report[39m
[36m[39m
```
## mkdocs
```
[31m │  ⚠  Warning from the Material for MkDocs team[0m
[31m │[0m
[31m │[0m  MkDocs 2.0, the underlying framework of Material for MkDocs,
[31m │[0m  will introduce backward-incompatible changes, including:
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
  - testing_setup.md
INFO    -  Documentation built in 0.13 seconds
```
