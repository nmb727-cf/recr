# TOS-REMAINING-CORE-MODULE-MAP-39

## 1. System Architecture

Shared layer name: `RemainingCoreModuleMapPrioritySequencingLayer`

Purpose:
- identify incomplete and missing core product modules across the Talent Operating System
- classify modules by criticality, phase bucket, implementation state, and blocker state
- sequence what must be built next using dependency-aware planning
- stay lightweight by extending the Core Module Registry instead of creating a separate planning product

Architecture layers:
- Discovery Layer
- Classification Layer
- Priority Layer
- Dependency Layer
- Gap Layer
- Sequencing Layer
- Planning Layer
- Audit Layer

## 2. Database Design

Primary entities:
- `tos_remaining_module_map`
- `tos_module_priority_record`
- `tos_module_gap_record`
- `tos_module_classification`
- `tos_module_sequence_plan`
- `tos_module_dependency_chain`
- `tos_module_build_recommendation`
- `tos_module_phase_mapping`
- `tos_module_continuation_note`
- `tos_module_planning_audit_log`

Tracked fields include:
- `module_key`
- `module_name`
- `module_domain`
- `classification_status`
- `priority_score`
- `mvp_status`
- `enterprise_status`
- `backend_gap_status`
- `frontend_gap_status`
- `dependency_chain_status`
- `blocker_reason`
- `recommended_next_action`
- `phase_bucket`
- `sequence_order`
- `owner_tool`
- `notes`

## 3. API Structure

Discovery APIs:
- scan remaining modules
- fetch remaining module map
- fetch module gaps
- fetch partially built modules
- fetch blocked modules
- fetch architecture-only modules

Priority APIs:
- fetch priority summary
- fetch next recommended modules
- fetch MVP-critical modules
- fetch enterprise-later modules

Sequencing APIs:
- create sequence plan
- fetch dependency chain
- fetch parallel-safe modules
- update continuation plan

## 4. Django Admin Configuration

Admin visibility is still Django Admin only.

Registered planning models:
- Remaining Module Map
- Module Priority Record
- Module Gap Record
- Module Classification
- Module Sequence Plan
- Module Dependency Chain
- Module Build Recommendation
- Module Phase Mapping
- Module Continuation Note
- Module Planning Audit Log

Admin supports:
- `list_display`
- `list_filter`
- `search_fields`
- ordering by `priority_score` and `sequence_order`
- inline gap records
- inline dependency chain
- inline continuation notes

## 5. Execution Flow

1. Read current module registry
2. Detect completed vs incomplete modules
3. Identify missing or architecture-only core areas
4. Classify modules by criticality and phase
5. Score priorities
6. Map dependency chains
7. Produce recommended next-build order
8. Store continuation notes
9. Use this planning layer as the next-build source of truth

## 6. Edge Cases

- module marked partial but actually abandoned
- module appears complete but frontend missing
- module has no owner and no blocker note
- module depends on untracked upstream work
- multiple AI tools building overlapping modules
- business rule unclear so module cannot be scored normally
- optional module mistaken as critical
- enterprise-only module wrongly inserted into MVP path

## 7. Priority / Sequencing Logic

Priority score is driven by:
- product criticality
- dependency weight
- user journey impact
- frontend gap severity
- backend gap severity
- blocker severity
- implementation readiness
- cross-system impact
- near-term usefulness

Immediate next-build focus should favor:
- ATS continuity gaps
- candidate lifecycle continuity
- workflow and submission completion
- ICC/HDC implementation closures
- cross-system automation / analytics / governance gaps that block runtime continuity

## 8. Integration Mapping

Consumes from:
- TOS Core Module Registry
- ICC module map
- HDC module map
- ATS core modules
- company / agency architecture
- candidate modules
- automation
- analytics
- governance
- audit

Produces:
- priority records
- dependency chain visibility
- continuation planning notes
- recommended next-build order
- admin-visible planning state for future prompts
