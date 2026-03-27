# Module Audit: candidates

## 1. Backend Files Found

* `apps/candidates/models.py`: Complex model with many fields for candidate state, source, and scoring.
* `apps/candidates/serializers.py`: Serializers for candidates, notes, profiles, and workflow policies.
* `apps/candidates/views.py`: Main views for candidate listing, database, and detail.
* `apps/candidates/urls.py`: Comprehensive URL patterns including CRM and Engagement sub-paths.
* `apps/candidates/identity_service.py`: Critical service for identity deduplication across Source 1, 2, and 3.
* `apps/candidates/protection.py`: Complex logic for candidate retention and exclusivity between agencies and companies.
* `apps/candidates/crm_views.py`: CRM-specific pipeline and interaction views.
* `apps/candidates/invite_views.py` & `apps/candidates/claim_views.py`: Handling candidate invite links and account "claims".

## 2. Frontend Usage Found

* `../frontend/src/api/candidates.ts`: Extensive integration for listing, profile, timeline, command-center, notes, skills, and invite-links.
* `../frontend/src/api/talentPools.ts`: Calls candidate-specific talent pool associations.
* `../frontend/src/api/crm.ts`: (Inferred) Likely calls CRM pipeline views.

## 3. Confirmed Backend Features

* **Identity Deduplication**: Multi-priority matching (email+phone, email, then phone) in `identity_service.py`.
* **Candidate Protection System**: Handles retention periods and exclusivity, blocking specific actions if protected.
* **Source Tracking**: Identifies if a candidate came from direct signup, agency submission, job board, etc.
* **Workflow Automation Policies**: Supports manual, semi-automated, and fully-automated workflows based on recruiter/team settings.
* **Note System**: Supports pinned, private, and context-specific (application/engagement) notes.
* **Timeline Logging**: `CandidateTimelineEvent` tracks candidate activity across the system.

## 4. Confirmed Frontend Features

* **Candidate Database**: Rich table with search, filters, and detail view integration.
* **Recruiter Surface**: "Active Work" surface for recruiters (board + focus + follow-up).
* **Command Center**: Sticky actions and tabbed interface for candidate details.
* **Identity Pre-checks**: Real-time checking if a user exists before registration.

## 5. Backend Without Frontend

* **Duplicate Merging**: `CandidateDuplicatesView` and `CandidateMergeView` are in backend but not clearly integrated into the primary candidates API file.
* **Export/Import**: Some backend support for importing/exporting candidates exists but may be missing from the UI.

## 6. Frontend Without Backend

* None identified. The backend provides a very rich API surface for all frontend candidate-related features.

## 7. Validation / Error Handling Gaps

* **Complex View Logic**: Views like `CandidateDetailView` are very large and handle multiple related objects (Profile, Workspace, Rights) in a single flow, making error recovery complex.
* **Protection Bypass Risks**: The protection system is complex; missing a `check_protected_action` call on a new candidate-related view could lead to business rule violations.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/candidates/`. This is a high-priority gap for such a core module.
* **Priority**: Unit tests for `identity_service.py` (matching logic) and integration tests for `protection.py` (retention rules).

## 9. Schema / API Documentation Gaps

* **Missing Detailed Schemas**: Major views (e.g., `CandidateListView`, `CandidateDatabaseView`) have generic "No response body" or simple success/error response descriptions in OpenAPI.
* **Undocumented Response Fields**: Many calculated fields in `CandidateSerializer` (e.g., `engagement_summary`) are not explicitly defined in the OpenAPI schema.

## 10. Security / Permission Concerns

* **Protection Logic Enforcement**: The system relies on manual calls to `check_protected_action`. An architectural review to enforce this at the model or serializer layer would be more robust.
* **Public Identity Check**: `check-identity/` is public. It returns whether a user or candidate exists. This could be used for account enumeration if not rate-limited.

## 11. Stability / Architecture Concerns

* **View Size**: `apps/candidates/views.py` is over 1800 lines. This is a potential maintenance risk and suggests the need for breaking down views into smaller mixins or service-oriented components.
* **Deep Coupling**: `Candidate` model is coupled with nearly every other module (Jobs, Pipeline, Agencies, RBAC, etc.).

## 12. Priority Fixes

### High
* **Implement Tests**: Add comprehensive test suite for identity matching and protection logic.
* **Refactor Large Views**: Split `views.py` into smaller files (e.g., `database_views.py`, `detail_views.py`, `engagement_views.py`).

### Medium
* **Enhance OpenAPI Documentation**: Add `@extend_schema` to major views to correctly describe return payloads.
* **Review Protection Enforcement**: Audit all candidate update/delete views for correct protection checks.

### Low
* **Centralize Choices**: Move field choices from `field_schema.py` and model classes to a more consistent registry if needed.

## 13. Unverified Items

* CRM suggest features (UNVERIFIED).
* Bulk merge operations UI (UNVERIFIED).

## 14. Recommended Next Tests

* `test_match_candidate_priority`: Verify email+phone match takes priority over email-only.
* `test_protection_retention_blocking`: Verify a company cannot view a candidate still in an agency's retention period (if configured).
* `test_link_user_to_candidate`: Verify correct linking of user accounts to existing candidate records during signup.
* `test_candidate_note_privacy`: Verify private notes are not visible to unauthorized users.
* `test_crm_pipeline_move`: Verify candidate stage transition in the CRM view.
