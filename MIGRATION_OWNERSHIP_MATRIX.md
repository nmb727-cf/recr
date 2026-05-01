# MIGRATION OWNERSHIP MATRIX

## 1. Platform Core Ownership
Handles cross-cutting infrastructure and foundational services.
*   **auth**, **rbac**, **notifications**, **i18n**, **global_config**, **security**, **audit**, **tenants**, **events**, **shared_master_data**

## 2. Domain Ownership
Encapsulates industry-specific business logic (e.g., ATS, Interviews, etc.). Domain engines must stay actor-neutral.
*   **ats**, **passport**, **interviews**, **communications**, **documents**, **analytics**, **automation**

## 3. Actors Ownership
Entity-specific logic for main system participants. Actor-specific UI/API logic belongs here.
*   **company**: (api, services, selectors, workflows)
*   **agency**: (api, services, selectors, workflows)
*   **candidate**: (api, services, selectors, workflows)

## 4. Bridge Ownership
Manages cross-entity logic and orchestration.
*   **company_agency**, **company_candidate**, **agency_candidate**, **tri_party**, **invite_flows**, **access_control**, **ownership_rules**, **sync_orchestration**

## 5. Legacy Rules
*   Stores pre-migration or not-yet-migrated code.
*   No new features should be added here.
*   Only temporary stabilization fixes are allowed.

## 6. Hard Rules
*   **Candidate is global**: Never owned by company or agency.
*   **Cross-entity logic belongs in bridge**: Never within an actor's domain.
*   **Shared infrastructure**: Belongs in `platform_core`.
*   **Actor-specific UI/API logic**: Belongs in `actors`.
*   **Domain engines must stay actor-neutral**.
*   **No new code in legacy**: Except for stabilization.
*   **No direct cross-actor imports**: Unless explicitly approved later.
