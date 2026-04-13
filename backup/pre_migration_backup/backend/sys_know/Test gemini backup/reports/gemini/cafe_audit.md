# Module Audit: cafe

## 1. Backend Files Found

* `apps/cafe/`: **EMPTY MODULE** (contains only `__init__.py`).
* **INTEGRATED LOGIC**: The "Cafe" functionality is currently integrated into other core modules.
* `apps/candidates/models.py`: Defines `cafe` as a candidate source.
* `apps/interviews/models.py`: Includes `is_cafe_interview` and `cafe_session_id` fields on the `Interview` model.

## 2. Frontend Usage Found

* **NONE**: No dedicated `cafe.ts` API file was found. References to Cafe likely exist within candidate and interview UI components as specific flags or source labels.

## 3. Confirmed Backend Features

* **Sourcing Attribution**: Ability to track candidates coming from the "Interview Café" channel.
* **Interview Specialisation**: Support for marking specific interviews as being part of a Cafe session for specialized reporting or UI handling.

## 4. Confirmed Frontend Features

* **NONE**: No standalone frontend features were identified.

## 5. Backend Without Frontend

* **Everything**: The concept of a "Cafe" exists in the data models but lacks a dedicated functional area in either the backend (views/urls) or frontend.

## 6. Frontend Without Backend

* None identified.

## 7. Validation / Error Handling Gaps

* **Incomplete implementation**: The empty `apps/cafe` module suggests a planned feature that has not yet been built or has been merged into other apps without removing the directory.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found for Cafe-specific logic.

## 9. Schema / API Documentation Gaps

* **Implicit Documentation**: Cafe fields are documented as part of the `Candidate` and `Interview` schemas, but their purpose and behavior are not explicitly described.

## 10. Security / Permission Concerns

* None identified beyond general interview and candidate security.

## 11. Stability / Architecture Concerns

* **Dead Code/Module**: The empty `apps/cafe` directory should be removed if the logic is intended to remain distributed across other apps.

## 12. Priority Fixes

### High
* **Clarify Strategy**: Decide whether Cafe should be a standalone app or an integrated feature and clean up the empty module accordingly.

### Medium
* **NONE**

### Low
* **NONE**

## 13. Unverified Items

* The intended workflow for a "Cafe Session" (UNVERIFIED).

## 14. Recommended Next Tests

* `test_candidate_source_cafe`: Verify that candidates can be correctly created with 'cafe' as their source.
* `test_interview_cafe_flag`: Verify that the `is_cafe_interview` flag is correctly persisted and retrieved.
