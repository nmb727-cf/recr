# Nightly Summary

## Pytest
```
E       RuntimeError: Database access not allowed, use the "django_db" mark, or the "db" or "transactional_db" fixtures to enable it.

venv/lib/python3.12/site-packages/django/db/backends/base/base.py:296: RuntimeError
----------------------------- Captured stdout call -----------------------------
Testing Duplicate Notification Status Codes (Expected 409)...
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________

Coverage HTML written to dir /home/nirav/projects/SaaS_Project/sys_know/generated/coverage/htmlcov
Coverage XML written to file /home/nirav/projects/SaaS_Project/sys_know/generated/coverage/coverage.xml
=========================== short test summary info ============================
FAILED backend/apps/interviews/tests/test_candidate_runtime_engine.py::CandidateRuntimeEngineTests::test_interview_opens
FAILED backend/apps/interviews/tests/test_candidate_runtime_engine.py::CandidateRuntimeEngineTests::test_join_works_and_status_updates
FAILED backend/apps/interviews/tests/test_decision_engine.py::InterviewDecisionEngineTests::test_multi_interviewer_evaluation_works
FAILED backend/apps/interviews/tests/test_security_engine.py::InterviewSecurityEngineTests::test_attempt_tracking_works
FAILED backend/apps/interviews/tests/test_security_engine.py::InterviewSecurityEngineTests::test_expiry_works
FAILED backend/apps/interviews/tests/test_security_engine.py::InterviewSecurityEngineTests::test_session_lock_works
FAILED backend/apps/interviews/tests/test_security_engine.py::InterviewSecurityEngineTests::test_token_validation_works
FAILED backend/test_duplicates.py::test_duplicate_notifications - RuntimeErro...
=================== 8 failed, 121 passed in 91.60s (0:01:31) ===================
```
## Schema
```
Warning: operationId "v1_interviews_scheduling_link_create" has collisions [('/api/v1/interviews/{id}/scheduling-link/', 'post'), ('/api/v1/interviews/scheduling-link/{token}/', 'post')]. resolving with numeral suffixes.
Warning: operationId "v1_interviews_flows_retrieve" has collisions [('/api/v1/interviews/flows/', 'get'), ('/api/v1/interviews/flows/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_interviews_questions_bank_retrieve" has collisions [('/api/v1/interviews/questions/bank/', 'get'), ('/api/v1/interviews/questions/bank/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_interviews_packages_retrieve" has collisions [('/api/v1/interviews/packages/', 'get'), ('/api/v1/interviews/packages/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_communications_messages_threads_retrieve" has collisions [('/api/v1/communications/messages/threads/', 'get'), ('/api/v1/communications/messages/threads/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_communications_communication_templates_retrieve" has collisions [('/api/v1/communications/communication/templates/', 'get'), ('/api/v1/communications/communication/templates/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_communications_communications_email_messages_retrieve" has collisions [('/api/v1/communications/communications/email-messages/', 'get'), ('/api/v1/communications/communications/email-messages/{id}', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_documents_documents_retrieve" has collisions [('/api/v1/documents/documents/', 'get'), ('/api/v1/documents/documents/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_documents_offers_retrieve" has collisions [('/api/v1/documents/offers/', 'get'), ('/api/v1/documents/offers/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_automation_rules_retrieve" has collisions [('/api/v1/automation/rules/', 'get'), ('/api/v1/automation/rules/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_candidate_applications_retrieve" has collisions [('/api/v1/candidate/applications/', 'get'), ('/api/v1/candidate/applications/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_prequalification_forms_retrieve" has collisions [('/api/v1/prequalification/forms/', 'get'), ('/api/v1/prequalification/forms/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_intelligence_prompts_retrieve" has collisions [('/api/v1/intelligence/prompts/', 'get'), ('/api/v1/intelligence/prompts/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_intelligence_automations_retrieve" has collisions [('/api/v1/intelligence/automations/', 'get'), ('/api/v1/intelligence/automations/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_intelligence_approvals_retrieve" has collisions [('/api/v1/intelligence/approvals/', 'get'), ('/api/v1/intelligence/approvals/{id}/', 'get')]. resolving with numeral suffixes.

Schema generation summary:
Warnings: 549 (368 unique)
Errors:   1798 (318 unique)

```
## Schemathesis
```
Failures:
  ❌ Server error: 8
  ❌ API accepted schema-violating request: 1
  ❌ API rejected schema-compliant request: 10
  ❌ Undocumented HTTP status code: 8

Errors:
  🚫 Network Error: 113

Warnings:
  ⚠️ Missing authentication: 236 operations returned only 401/403 responses
  ⚠️ Missing valid test data: 180 operations repeatedly returned 404 responses
  ⚠️ Schema validation mismatch: 453 operations mostly rejected generated data

Test cases:
  30800 generated, 19 found 27 unique failures, 1778 skipped

Seed: 88076271192833566827489686104300716352

=============== 27 failures, 113 errors, 3 warnings in 2962.96s ================
```
## Vitest
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
## Playwright
```

Running 1 test using 1 worker

[1A[2K[1/1] tests/smoke.spec.ts:3:1 › app loads
[1A[2K  1 passed (2.4s)
```
