# TOS-NEXT-MODULE-IMPLEMENTATION-PROMPT-41

## 1. System Architecture

Shared layer name: `ImplementationPromptGeneratorLayer`

Purpose:
- resolve the selected next core module from the selection layer
- assemble a copy-ready implementation prompt with architecture, backend, UI, API, dependency, and integration context
- save prompt versions and audit history
- keep visibility lightweight through Django Admin only

Architecture layers:
- Context Layer
- Resolution Layer
- Scope Layer
- Assembly Layer
- Audit Layer

## 2. Database Design

Primary entities:
- `tos_generated_prompt`
- `tos_prompt_context`
- `tos_prompt_dependency`
- `tos_prompt_scope`
- `tos_prompt_history`
- `tos_prompt_version`

Tracked fields include:
- `prompt_id`
- `module_key`
- `prompt_title`
- `prompt_scope`
- `prompt_dependencies`
- `prompt_status`
- `prompt_version`
- `generated_by`
- `approved_by`
- `created_at`
- `updated_at`

## 3. API Structure

Generation APIs:
- generate implementation prompt
- fetch generated prompt
- regenerate prompt
- fetch prompt history
- approve prompt
- lock prompt

Context APIs:
- fetch selected module
- fetch module dependencies
- fetch module context
- fetch integration mapping

## 4. Django Admin Configuration

Admin visibility is still Django Admin only.

Registered prompt models:
- Generated Prompt
- Prompt Context
- Prompt Dependency
- Prompt Scope
- Prompt History
- Prompt Version

Admin supports:
- viewing generated prompts
- viewing prompt history
- viewing dependencies and scopes
- checking approval and lock state

## 5. Execution Flow

1. Read selected module
2. Load module context
3. Load dependencies
4. Build scope
5. Build UI requirements
6. Build backend requirements
7. Build API requirements
8. Build integration mapping
9. Assemble prompt
10. Save generated prompt and version history
11. Send prompt to Codex

## 6. Edge Cases

- module missing context
- dependency missing
- module selection changed
- prompt regenerated
- version conflict

## 7. Integration Mapping

Consumes from:
- Module Registry
- Remaining Module Map
- Next Module Selection
- dependency and follow-up sequencing records

Produces:
- copy-ready implementation prompt
- prompt history and versions
- prompt lock/approval state
- Codex-ready next implementation artifact

## 8. Generated Implementation Prompt

Selected module:
- `workflow_system`

Recommended build mode:
- `backend_first`

Immediate implementation prompt generated for the workflow system core execution layer.
