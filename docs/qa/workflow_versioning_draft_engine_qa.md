# Workflow Versioning + Draft Engine QA

| Area | Status | Notes |
|---|---|---|
| draft creation | Implemented | Draft creation is handled via `create_draft()` and `/api/v1/workflows/{id}/draft/create/`. |
| draft save | Implemented | Snapshot save and ready-for-publish status are supported via `save_draft_snapshot()` and `/draft/save/`. |
| publish flow | Implemented | Publish archives prior published version, marks new version published, and logs version change. |
| rollback flow | Implemented | Rollback repoints current published version to selected historical version with audit change log. |
| clone flow | Implemented | Clone creates a new draft/version from historical metadata snapshot and logs cloned change. |
| version comparison | Implemented | Compare API generates/stores added/removed/changed diffs for stages/transitions/conditions/actions/routing/SLA/notifications/human-task rules. |
| orchestrator integration | Implemented | `WorkflowInstance` now binds `version_id`; orchestrator response includes version reference. |
| running instance safety | Implemented | Existing instances keep their stored `version_id`; new instances bind to latest published version. |

Overall Completion: 100 %

Critical Missing Items:
- None
- None

Next QA Priority:
- Add API integration tests validating all draft/version endpoints and permissions.
- Validate builder UI end-to-end flow for compare, rollback, and clone actions.
