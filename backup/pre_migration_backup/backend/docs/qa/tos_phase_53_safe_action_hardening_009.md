# TOS Phase 53: Safe Action Hardening 009

## Scope
This phase locks the current safe action hardening milestone before any further breadth expansion.

The goal of this layer is to keep `orchestration_center` orchestration-only while routing business-state mutation through owner-module contracts with normalized context/result handling.

## What Was Hardened
- shared owner contract primitives in `shared.owner_contracts`
- normalized `OwnerActionContext`
- normalized `OwnerActionResult`
- normalized `OwnerContractError` categories
- executor-side serialization through `as_execution_payload(...)`
- tenant-scoped duplicate suppression and retry-safe/no-op handling
- non-blocking failure recording in orchestration execution results

## Safe Actions Following The Shared Contract/Result Pattern
These action paths now use owner contracts and return normalized owner results that orchestration serializes:

- `create_deadline`
  - owner: `pipeline`
  - contract: `PipelineDeadlineService.create_from_orchestration(...)`
- `notify`
  - owner: `communications`
  - contracts:
    - `CommunicationDispatchService.notify_from_orchestration(...)`
    - `CommunicationDispatchService.enqueue_email_from_orchestration(...)`
- `enqueue_communication`
  - owner: `communications`
  - contracts:
    - email queue through `CommunicationDispatchService.enqueue_email_from_orchestration(...)`
    - in-app notification through `CommunicationDispatchService.notify_from_orchestration(...)`
- `create_review_task`
  - owner: `interviews`
  - contract: `InterviewReviewTaskService.create_from_orchestration(...)`
- `escalate`
  - owner result anchored in `pipeline`
  - composed owner contracts:
    - `PipelineDeadlineService.escalate_from_orchestration(...)`
    - `CommunicationDispatchService.notify_from_orchestration(...)`
- `assign`
  - owner modules currently covered:
    - `pipeline`
    - `interviews`
    - `candidates`
    - `agencies`
- `mark_flag`
  - owner modules currently covered:
    - `pipeline`
    - `interviews`
    - `candidates`
    - `agencies`

## Owner-Module Contract Boundaries
- Orchestration builds `OwnerActionContext` and passes tenant, actor, external reference, and audit metadata.
- Owner modules validate ownership and mutate only owner-owned records.
- Owner modules return `OwnerActionResult`; orchestration persists only normalized execution payloads.
- Duplicate-safe no-op outcomes return `duplicate=True`.
- Validation, ownership, not-found, unsupported, and transient failures are mapped through `OwnerContractError`.
- `schedule_followup` remains a safe orchestration scheduling primitive, not a direct owner mutation contract.

## Retry, Error, And Idempotency Semantics
- Idempotency is driven by stable external references and tenant-scoped dedupe keys.
- Duplicate-safe replays serialize as `status=deduplicated`.
- `retry_safe=True` is preserved for transient failures and duplicate-safe owner outcomes.
- Validation, ownership, not-found, and unsupported failures are intentionally non-retry-safe.
- Orchestration keeps failures non-blocking and records structured action results plus audit entries.
- Scheduled downstream action failures remain visible on the scheduled action row and the parent execution result.

## What Remains Intentionally Stubbed
- unsupported owner targets still return `stubbed_unbound` instead of mutating state
- unsupported communication channels outside the hardened contracts remain unbound
- no broad orchestration event expansion is part of this milestone
- no direct orchestration writes into owner-owned business state
- no attempt to generalize beyond the currently proven owner modules/actions

## Boundaries Explicitly Preserved
- `orchestration_center` remains orchestration-only
- owner modules remain the only writers of owner-owned state
- tenant isolation remains authoritative at every contract edge
- retry and duplicate behavior remain tenant-scoped
- hardening is considered sufficient for the current platform stage and is intentionally paused here
