# Owner Contract Template

All new orchestration-to-owner bindings should follow this pattern:

1. Orchestration builds a `shared.owner_contracts.OwnerActionContext`.
2. The owner module exposes a narrow `*_from_orchestration(...)` contract method with the shared leading signature: `(*, context: OwnerActionContext, ...)`.
3. The owner method validates tenant ownership and mutates only owner-owned state.
4. The owner method returns `shared.owner_contracts.OwnerActionResult`.
5. Duplicate and retry-safe no-op outcomes return `duplicate=True`.
6. Validation, ownership, missing-target, or unsupported-operation failures raise `shared.owner_contracts.OwnerContractError`.
7. Orchestration serializes the result and keeps failures non-blocking.

Normalized context contract:

- `tenant_id`: authoritative tenant boundary for the owner module
- `actor_id`: actor or automation initiator
- `external_source`: defaults to `orchestration_center`
- `external_reference`: stable idempotency/reference key for retries
- `audit_metadata`: owner-safe audit payload such as `automation_run_id`, `rule_id`, `source_event`, `assignment_reason`, `flag_reason`

Normalized result contract:

Required result fields:

- `owner_module`
- `action_family`
- `status`
- `target_type`
- `target_id`
- `duplicate`
- `retry_safe`
- `audit_metadata`
- `payload`

Execution serialization rules:

- `result.execution_status()` returns `deduplicated` when `duplicate=True`, otherwise the native result status such as `completed` or `queued`
- `result.as_execution_payload(action_type=...)` is the only shape orchestration should persist into `action_results_json`
- owner-specific ids may appear in `payload` and are flattened into the execution payload for compatibility

Standard error categories:

- `owner_contract_validation`: malformed ids, missing required inputs, invalid payload shape
- `owner_contract_ownership`: cross-tenant recipient/assignee/relationship violations
- `owner_contract_not_found`: owner-owned target record not found in the tenant scope
- `owner_contract_unsupported`: intentionally unsupported entity types or flags
- `owner_contract_transient`: retry-safe downstream/transient owner failure
