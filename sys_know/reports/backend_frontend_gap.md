# Nightly Summary

## pytest
```
configfile: pytest.ini
testpaths: backend
plugins: schemathesis-4.14.0, django-4.12.0, base-url-2.1.0, hypothesis-6.151.9, playwright-0.7.2, anyio-4.13.0, cov-7.1.0
collected 1130 items / 1 error

==================================== ERRORS ====================================
_____ ERROR collecting backend/apps/pipeline/tests/test_stage_ownership.py _____
ImportError while importing test module '/home/nirav/projects/SaaS_Project/backend/apps/pipeline/tests/test_stage_ownership.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
backend/apps/pipeline/tests/test_stage_ownership.py:11: in <module>
    from apps.pipeline.views import (
E   ImportError: cannot import name 'validate_application_move' from 'apps.pipeline.views' (/home/nirav/projects/SaaS_Project/backend/apps/pipeline/views.py)
=========================== short test summary info ============================
ERROR backend/apps/pipeline/tests/test_stage_ownership.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.02s ===============================
```
## schema
```
Warning: operationId "v1_workflow_instances_notifications_retrieve" has collisions [('/api/v1/workflow/instances/{id}/notifications/', 'get'), ('/api/v1/workflow-instances/{id}/notifications/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_instances_recovery_retrieve" has collisions [('/api/v1/workflow/instances/{id}/recovery/', 'get'), ('/api/v1/workflow-instances/{id}/recovery/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_instances_retry_create" has collisions [('/api/v1/workflow/instances/{id}/retry/', 'post'), ('/api/v1/workflow-instances/{id}/retry/', 'post')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_instances_scheduled_tasks_retrieve" has collisions [('/api/v1/workflow/instances/{id}/scheduled-tasks/', 'get'), ('/api/v1/workflow-instances/{id}/scheduled-tasks/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_instances_sla_retrieve" has collisions [('/api/v1/workflow/instances/{id}/sla/', 'get'), ('/api/v1/workflow-instances/{id}/sla/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_instances_stages_retrieve" has collisions [('/api/v1/workflow/instances/{id}/stages/', 'get'), ('/api/v1/workflow-instances/{id}/stages/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_instances_timeline_retrieve" has collisions [('/api/v1/workflow/instances/{id}/timeline/', 'get'), ('/api/v1/workflow-instances/{id}/timeline/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_instances_wait_states_retrieve" has collisions [('/api/v1/workflow/instances/{id}/wait-states/', 'get'), ('/api/v1/workflow-instances/{id}/wait-states/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_scheduler_tasks_retrieve" has collisions [('/api/v1/workflow-scheduler/tasks/', 'get'), ('/api/v1/workflow-scheduler/tasks/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_conditions_retrieve" has collisions [('/api/v1/workflow-conditions/', 'get'), ('/api/v1/workflow-conditions/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_condition_groups_retrieve" has collisions [('/api/v1/workflow-condition-groups/', 'get'), ('/api/v1/workflow-condition-groups/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_actions_retrieve" has collisions [('/api/v1/workflow-actions/', 'get'), ('/api/v1/workflow-actions/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_human_tasks_retrieve" has collisions [('/api/v1/workflow-human-tasks/', 'get'), ('/api/v1/workflow-human-tasks/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_versions_retrieve" has collisions [('/api/v1/workflow-versions/', 'get'), ('/api/v1/workflow-versions/{id}/', 'get')]. resolving with numeral suffixes.
Warning: operationId "v1_workflow_templates_retrieve" has collisions [('/api/v1/workflow-templates/', 'get'), ('/api/v1/workflow-templates/{id}/', 'get')]. resolving with numeral suffixes.

Schema generation summary:
Warnings: 1530 (879 unique)
Errors:   3620 (700 unique)

```
## schemathesis
```
  ❌ Server error: 8
  ❌ API accepted schema-violating request: 1
  ❌ API rejected schema-compliant request: 22
  ❌ Undocumented HTTP status code: 20
  ❌ Unsupported methods: 2

Errors:
  🚫 Runtime Error: 1

Warnings:
  ⚠️ Missing authentication: 859 operations returned only 401/403 responses
  ⚠️ Missing valid test data: 487 operations repeatedly returned 404 responses
  ⚠️ Schema validation mismatch: 1292 operations mostly rejected generated data

Test cases:
  137849 generated, 33 found 53 unique failures

Seed: 176149374238302745076848674645232544818

================= 53 failures, 1 error, 3 warnings in 8449.79s =================
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
[1A[2K  1 passed (2.1s)
```
## mkdocs
```

```
