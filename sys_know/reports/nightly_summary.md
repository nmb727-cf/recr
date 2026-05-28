# Nightly Summary

## Pytest
```
ERROR backend/apps/workflow_execution/tests/test_workflow_sla_engine.py::TestWorkflowSLAEngine::test_3_breach_reached_breach_event
ERROR backend/apps/workflow_execution/tests/test_workflow_sla_engine.py::TestWorkflowSLAEngine::test_4_escalation_reached_escalation_triggered
ERROR backend/apps/workflow_execution/tests/test_workflow_sla_engine.py::TestWorkflowSLAEngine::test_5_stage_completes_sla_resolved
ERROR backend/apps/workflow_execution/tests/test_workflow_template_engine.py::TestWorkflowTemplateEngine::test_1_create_template_saved
ERROR backend/apps/workflow_execution/tests/test_workflow_template_engine.py::TestWorkflowTemplateEngine::test_2_apply_template_creates_workflow
ERROR backend/apps/workflow_execution/tests/test_workflow_template_engine.py::TestWorkflowTemplateEngine::test_3_clone_template_creates_new_template
ERROR backend/apps/workflow_execution/tests/test_workflow_template_engine.py::TestWorkflowTemplateEngine::test_4_import_template_valid_template_created
ERROR backend/apps/workflow_execution/tests/test_workflow_template_engine.py::TestWorkflowTemplateEngine::test_5_export_template_json_generated
ERROR backend/apps/workflow_execution/tests/test_workflow_template_engine.py::TestWorkflowTemplateEngine::test_6_system_templates_seeded
ERROR backend/apps/workflow_execution/tests/test_workflow_versioning_engine.py::TestWorkflowVersioningEngine::test_1_user_edits_published_workflow_creates_draft_live_untouched
ERROR backend/apps/workflow_execution/tests/test_workflow_versioning_engine.py::TestWorkflowVersioningEngine::test_2_publish_draft_creates_new_published_version
ERROR backend/apps/workflow_execution/tests/test_workflow_versioning_engine.py::TestWorkflowVersioningEngine::test_3_rollback_to_older_version_logged
ERROR backend/apps/workflow_execution/tests/test_workflow_versioning_engine.py::TestWorkflowVersioningEngine::test_4_compare_two_versions_generates_diff
ERROR backend/apps/workflow_execution/tests/test_workflow_versioning_engine.py::TestWorkflowVersioningEngine::test_5_existing_instance_keeps_version_after_new_publish
ERROR backend/apps/workflow_execution/tests/test_workflow_visual_builder_engine.py::TestWorkflowVisualBuilderEngine::test_1_create_simple_workflow_nodes_saved
ERROR backend/apps/workflow_execution/tests/test_workflow_visual_builder_engine.py::TestWorkflowVisualBuilderEngine::test_2_connect_nodes_connection_created
ERROR backend/apps/workflow_execution/tests/test_workflow_visual_builder_engine.py::TestWorkflowVisualBuilderEngine::test_3_decision_node_multiple_paths_valid
ERROR backend/apps/workflow_execution/tests/test_workflow_visual_builder_engine.py::TestWorkflowVisualBuilderEngine::test_4_invalid_workflow_returns_validation_error
ERROR backend/apps/workflow_execution/tests/test_workflow_visual_builder_engine.py::TestWorkflowVisualBuilderEngine::test_5_end_to_end_workflow_execution_compatible
====== 21 failed, 35 passed, 1 warning, 1110 errors in 238.56s (0:03:58) =======
```
## Schema
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
Warnings: 1537 (883 unique)
Errors:   3648 (704 unique)

```
## Schemathesis
```
  ❌ Server error: 9
  ❌ API accepted schema-violating request: 1
  ❌ API rejected schema-compliant request: 12
  ❌ Undocumented HTTP status code: 22
  ❌ Unsupported methods: 2

Errors:
  🚫 Runtime Error: 1

Warnings:
  ⚠️ Missing authentication: 870 operations returned only 401/403 responses
  ⚠️ Missing valid test data: 503 operations repeatedly returned 404 responses
  ⚠️ Schema validation mismatch: 1299 operations mostly rejected generated data

Test cases:
  138697 generated, 33 found 46 unique failures

Seed: 198985161985024240562614982152074554599

================ 46 failures, 1 error, 3 warnings in 13397.57s =================
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
[1A[2K  1 passed (4.7s)
```
