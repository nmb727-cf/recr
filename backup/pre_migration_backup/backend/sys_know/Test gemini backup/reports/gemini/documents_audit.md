# Module Audit: documents

## 1. Backend Files Found

* `apps/documents/models.py`: Defines `Document` and `OfferLetter` models with entity linkage and status lifecycles.
* `apps/documents/serializers.py`: Serializers for managing document metadata and offer details.
* `apps/documents/views.py`: Comprehensive views for document listing, uploading, downloading, and offer letter workflows (approval, send, accept/reject).
* `apps/documents/urls.py`: Unified URL patterns for the document and offer management system.

## 2. Frontend Usage Found

* **CRITICAL GAP**: No dedicated API file for `documents` was found in `../frontend/src/api/`. This module appears to be implemented in the backend but not yet integrated into the frontend API layer.

## 3. Confirmed Backend Features

* **Universal Document Linkage**: Flexible system for attaching files to candidates, applications, jobs, or organisations.
* **Specialised Offer Lifecycle**: Multi-step hiring offer workflow (Draft -> Pending Approval -> Approved -> Sent -> Accepted/Rejected/Revoked).
* **Document Versioning**: Basic support for tracking file versions (`version` field) and marking the current active document (`is_current` flag).
* **Verification Status**: Support for recording document verification metadata (`is_verified`, `verified_by`, `verified_at`).
* **Entity Isolation**: Documents are scoped to specific entities (entity_type/entity_id) within a tenant.

## 4. Confirmed Frontend Features

* **NONE**: No frontend integration was identified for the documents module.

## 5. Backend Without Frontend

* **Everything**: The entire document management and offer letter system exists solely in the backend without corresponding frontend API support.

## 6. Frontend Without Backend

* None identified.

## 7. Validation / Error Handling Gaps

* **Placeholder Download Logic**: `DocumentDownloadView` lacks secure presigned URL generation (marked as TODO) and simply returns the raw `file_url`.
* **Conflict Prevention**: There is no logic to prevent creating multiple active offer letters for the same application.
* **Upload Validation**: File size and MIME type validation are handled by the model fields but lack granular error feedback in the API layer.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/documents/`.
* **Priority**: Integration tests for the offer letter status machine and secure document download access.

## 9. Schema / API Documentation Gaps

* **Generic API Views**: The views lack `@extend_schema` decorators, resulting in incomplete OpenAPI documentation for response formats and error cases.

## 10. Security / Permission Concerns

* **Insufficient Resource Scoping**: Current views only require `IsAuthenticated`. There is no check to ensure the user has specific permissions (e.g., HR role) to view sensitive documents (Offer Letters, ID Proofs) within their tenant.
* **Insecure File URLs**: The system currently returns the raw `file_url`. If these URLs are not properly protected (e.g., via S3/MinIO policies), they could be accessible to unauthorized external actors.

## 11. Stability / Architecture Concerns

* **Fragmented Storage Logic**: The `documents` module is standalone, but many other modules (Candidates, Jobs, Passport) also handle their own file references, leading to fragmented file management patterns.
* **Hardcoded Entities**: The set of allowed entity types (Candidate, Job, etc.) is hardcoded in the model choices, limiting future expansion without migrations.

## 12. Priority Fixes

### High
* **Implement Frontend API**: Create `frontend/src/api/documents.ts` to expose the document and offer management features to the UI.
* **Secure Document Downloads**: Implement robust presigned URL generation for secure file access.
* **Enforce Granular Permissions**: Restrict access to sensitive document types (Offers, ID Proofs) based on user roles (e.g., HR Managers only).

### Medium
* **Implement Tests**: Add comprehensive test suite for the offer lifecycle and document versioning.
* **Enhance OpenAPI Documentation**: Add detailed schemas for all document-related endpoints.

### Low
* **Standardize File Management**: Consider unifying file storage across all apps through the `documents` module to avoid duplication.

## 13. Unverified Items

* Integration with cloud storage (S3/MinIO) (UNVERIFIED — marked as TODO).
* Support for document expiration notifications (UNVERIFIED).

## 14. Recommended Next Tests

* `test_offer_letter_approval_flow`: Verify that an offer cannot be sent until it is marked as approved.
* `test_candidate_offer_rejection_reason`: Verify that rejection reasons are correctly captured and stored when a candidate rejects an offer.
* `test_document_versioning_increment`: Verify that uploading a new version of a document correctly increments the version number.
* `test_unauthorised_document_access`: Verify that a user cannot access documents belonging to a different tenant.
* `test_secure_download_url_generation`: Verify that the download endpoint correctly generates a temporary secure access link (once implemented).
