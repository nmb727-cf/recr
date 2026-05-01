# Agency Candidate CRM Design Document

## 1. Overview
The Agency Candidate CRM is a specialized Talent CRM designed for staffing agencies to source, manage, and nurture their talent pool independently of specific job openings, while maintaining seamless integration with the core Talent Operating System.

## 2. Architecture Design
The module follows a **Layered Overlay Architecture**:

- **Core Layer (Global):** Uses the existing `Candidate` entity as the source of truth for person-level data (name, email, skills, experience).
- **Agency Layer (Overlay):** Uses `AgencyCandidate` to store agency-specific CRM data (recruiter ownership, agency-specific status, pipeline stage, hotlists).

This ensures that an agency can build its own private database of candidates without affecting the core `Candidate` record used by other modules or tenants.

## 3. Database Models

### AgencyCandidate
Overlay entity linking a global candidate to an agency tenant.
- `candidate`: ForeignKey(Candidate)
- `owner`: ForeignKey(User)
- `pipeline_stage`: ForeignKey(AgencyCandidatePipelineRegistry)
- `status`: [Active, Dormant, Placed, Blacklisted]
- `availability`: [Immediate, 15 Days, 30 Days, 60 Days, Not Available]
- `source`: [LinkedIn, Job Portal, Referral, Internal Database, etc.]

### AgencyCandidatePipelineRegistry
Registry-driven pipeline stages.
- `stage_key`: unique identifier (e.g., `screened`)
- `stage_label`: display name (e.g., `Screened`)
- `order`: sorting order

### AgencyCandidateOwnership
Tracks recruiter ownership history and period.

### AgencyCandidateHotlist
Group candidates into custom lists (e.g., "Top Java Devs", "Ready for Q2").

### AgencyCandidateResumeVersion
Manages multiple resume versions and recruiter-formatted summaries.

### AgencyCandidateSubmission
Tracks submissions to client tenants and jobs.

## 4. API Structure (REST)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/agency-candidates/candidates/` | GET | List talent pool with filters |
| `/api/v1/agency-candidates/candidates/` | POST | Add candidate to CRM |
| `/api/v1/agency-candidates/candidates/{id}/change_stage/` | POST | Move candidate in pipeline |
| `/api/v1/agency-candidates/candidates/{id}/transfer_ownership/` | POST | Change recruiter owner |
| `/api/v1/agency-candidates/hotlists/` | GET/POST | Manage hotlists |
| `/api/v1/agency-candidates/submissions/` | POST | Submit candidate to client job |

## 5. UI Structure

The Agency Candidate CRM frontend will be implemented within the Agency Workspace, following the TalentOS design system.

### Pages & Components
1. **Talent Pool (List View)**
   - High-performance table with server-side filtering.
   - Filters: Pipeline Stage, Availability, Owner, Source, Tags.
   - Actions: Bulk Hotlist, Bulk Assign, Quick Add.

2. **Candidate Profile (Detail View)**
   - **Header:** Quick stats (Status, Owner, Last Contacted).
   - **Summary Tab:** Candidate bio, skills, and current overlay data.
   - **Pipeline Tab:** Visual stage tracker and stage history.
   - **Resume Tab:** Version management, formatted resume viewer, and summary editor.
   - **Activity Tab:** Timeline of all agency interactions and client submissions.
   - **Notes Tab:** Recruiter-specific nurture notes.

3. **Pipeline View (Kanban)**
   - Drag-and-drop board based on the `AgencyCandidatePipelineRegistry`.
   - Cards showing candidate summary, owner, and availability.

4. **Hotlists (Dashboard & List)**
   - Sidebar for quick access to personal and team hotlists.
   - Drag-and-drop adding to hotlists.

### Sourcing Modal
- **Quick Add:** Mini-form for Name, Email, Phone, and Source.
- **Resume Upload:** File dropzone that triggers background parsing and core candidate creation.

## 6. Implementation Plan

### Phase 1: Foundation (Current)
- [x] Database models and migrations.
- [x] Service layer for core logic (Create, Transfer, Submit).
- [x] REST API ViewSets and Serializers.
- [x] RBAC permission registry and role mapping.
- [x] Registry-driven pipeline seeding.

### Phase 2: Engagement & Sourcing
- [ ] Integration with Resume Parsing engine for "Upload and Add".
- [ ] Bulk import service for CSV/Excel sourcing.
- [ ] Automatic "Follow-up Due" triggers based on nurture notes.

### Phase 3: Intelligence & Analytics
- [ ] Submission success rate tracking per recruiter.
- [ ] Talent pool diversity and availability dashboards.
- [ ] AI-driven matching of CRM candidates to assigned jobs.

## 7. Flow Logic
... (keep existing flow logic) ...

## 8. RBAC & Permissions
... (keep existing RBAC table) ...

## 9. QA Documentation
... (keep existing QA scenarios) ...
