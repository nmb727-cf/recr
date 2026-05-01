# MIGRATION SUMMARY

The architectural migration of Talentos to a modular structure is now complete and stabilized.

## Phases Completed
1.  **Phase 1: Skeleton Creation** - Established the folder structure.
2.  **Phase 2: Platform Core Extraction** - Relocated backend and frontend infrastructure.
3.  **Phase 3: Actor Boundary Mapping & Extraction** - Separated Company, Agency, and Candidate entry points.
4.  **Phase 4: Bridge Module Extraction** - Moved cross-entity relationship and invitation logic.
5.  **Phase 5: Stabilization & Lock** - Final import verification and architectural enforcement.

## Key Relocations
*   **Infrastructure**: Moved to `platform_core/` (Auth, Tenants, RBAC, i18n).
*   **Actors**: `organisations` moved to `actors/company`, `agencies/talent_pools` moved to `actors/agency`, `passport` moved to `actors/candidate`.
*   **Bridge**: Relationship services and candidate protection rules moved to `bridge/`.

## Compatibility Strategy
*   Used **thin wrappers** in all original backend locations (`from apps.X.Y import *`).
*   Used **re-exporting wrappers** in frontend pages and components.
*   Preserved all existing imports to prevent project-wide breakage.

## Remaining Deferred Items
*   **Domain Models**: Database models remain in original apps to preserve table names and foreign keys.
*   **Mixed Logic in domain/apps**: Some complex views involving heavy domain integration await Phase 6 domain cleanup.

## Risks
*   **Wrapper Reliance**: The system currently relies on compatibility wrappers. Future phases should gradually update all imports to direct paths.
*   **Circular Imports**: Modular boundaries are new; developers must be vigilant about not re-introducing cross-actor imports.
