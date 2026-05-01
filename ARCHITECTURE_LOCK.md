# ARCHITECTURE LOCK: Talentos Modular System

This document defines the strict architectural boundaries for the Talentos codebase. All future changes must adhere to these rules.

## 1. Actor Boundaries
*   **actors/company**: Owns company-facing UI, APIs, and workflows.
*   **actors/agency**: Owns agency-facing UI, APIs, and CRM/talent-pool flows.
*   **actors/candidate**: Owns candidate-facing self-service and profile flows.
*   **No Cross-Actor Logic**: Logic specific to one actor must not reside in or be imported directly by another actor.

## 2. Cross-Entity Logic (Bridge)
*   **bridge/**: All interactions between different entities (e.g., Company ↔ Agency, Company ↔ Candidate) must reside here.
*   Bridge modules manage invitations, ownership rules, and synchronization.

## 3. Shared Infrastructure (Platform Core)
*   **platform_core/**: Foundational services including Auth, RBAC, i18n, Security, and multi-tenancy mechanisms.
*   Actor-neutral and domain-agnostic.

## 4. Business Engines (Domain)
*   **domain/**: Core business logic and shared engines (ATS, Interviews, Communications).
*   Engines must stay actor-neutral and serve multiple actors via the Bridge or direct Actor APIs.

## 5. Legacy Code
*   **legacy/**: Temporary area for unmigrated code.
*   **Strict Freeze**: No new features allowed in legacy folders. Only critical bug fixes.

## 6. Hard Rules
*   **Candidate is global**: Never owned exclusively by company or agency.
*   **No circular imports** between major architectural layers.
*   **Actor-specific logic belongs in actors**, never in the core domain engines.
