# Agency Architecture Reset Document (TOS-AGENCY-RESET-001)

## 1. Agency Philosophy: Staffing CRM vs. Corporate ATS
| Feature | Company Side (ATS) | Agency Side (CRM/ERP) |
|---------|-------------------|----------------------|
| **Primary Object** | The Job Requisition | The Candidate (Talent Pool) |
| **Workflow** | Linear Pipeline (Applied -> Hired) | Circular Nurture (Source -> Pool -> Map -> Submit -> Reuse) |
| **Ownership** | Hiring Manager / Recruiter | Individual Recruiter / Account Manager (Protected) |
| **Goal** | Fill a vacancy | Build a high-yield talent database & client portfolio |
| **Visibility** | Open to HR Team | Strictly controlled by Ownership/Team rules |

## 2. Agency Domains & Module Map

### A. Agency Candidate Management (Staffing CRM)
**Core Intent:** Building a "Gold Mine" of talent.
- **Talent Pool:** Deeply segmented database with proprietary metadata (Readiness, Sentiment).
- **Recruiter Workbench:** A personalized cockpit for daily sourcing and nurture tasks.
- **Hotlists:** Dynamic "shopping carts" of talent for specific categories or upcoming needs.
- **Resume System:** Proprietary "Formatted Resumes" (removing contact info, adding agency branding).
- **Reuse Intelligence:** Tracking how many times a candidate has been submitted/rejected across different clients.

### B. Agency Client Management (Account CRM)
**Core Intent:** Managing the revenue source.
- **Platform Clients:** Companies already on the TalentOS network (shared jobs/apps).
- **External Clients:** Companies not on the TOS (managed manually by agency).
- **Requirements/SLAs:** Managing commercial terms per client relationship.

### C. Agency Job Management (Assignment Engine)
- **Scenario 1 (Platform Job):** Assigned by a TOS Company. Limited control over stages.
- **Scenario 2 (External Job):** Manually created by Agency. Full control over the workflow.
- **Scenario 3 (Internal Job):** Agency hiring for itself (Minimal ATS flow).

### D. Agency Internal ERP (Operations)
- **Workload Management:** Monitoring recruiter targets and submission volumes.
- **Team Workspace:** Collaboration tools for shared candidate pools.
- **Performance Analytics:** Revenue per recruiter, time-to-submit, and client satisfaction.

## 3. Information Architecture (Navigation Structure)

- **Staffing Desk (Dashboard)** - Quick actions, today's follow-ups, hotlist updates.
- **Talent CRM**
    - Talent Pool (Database)
    - Hotlists
    - Sourcing (Resume Parser / Quick Add)
- **Client Desk**
    - Client Portfolio
    - Requirements / Scoping
- **Assignments (Jobs)**
    - Assigned Jobs (Platform)
    - Direct Jobs (External)
    - Submission Tracker
- **Recruiter Ops (ERP)**
    - My Tasks / Follow-ups
    - Team Performance
- **Agency Settings**
    - Pipeline Registry
    - Resume Templates
    - Ownership Rules

## 4. Shared vs. Agency-Specific Logic Map

### Shared Reusable Engines
- `candidates.Candidate`: Core person entity (Email, Phone, Basic Bio).
- `notifications`: Notification dispatch logic.
- `communications`: Email/WhatsApp/In-app message delivery.
- `rbac`: Permission checking framework.
- `translations`: i18n key management.

### Agency-Specific Implementations
- `agency_candidates`: The **CRM Overlay**.
- `agency_candidates.ResumeFormatter`: Logic to strip/brand resumes.
- `agency_candidates.OwnershipEngine`: Time-based ownership protection.
- `agency_clients`: Managed relationships and external client data.
- `agency_submissions`: Specialized cross-tenant submission logic.

## 5. Implementation Order & Boundaries

1. **Hard Isolation:** Ensure `AgencyCandidate` does not use `pipeline.Application` for internal CRM states.
2. **Staffing CRM Foundation:** Finalize `AgencyCandidate` with Readiness, Availability, and Ownership.
3. **Registry Hardening:** Ensure `AgencyCandidatePipelineRegistry` is distinct from Company ATS stages.
4. **Client Management:** Implement External Client and SLA tracking.
5. **Resume Workflow:** Implement the "Secure/Formatted Resume" versioning system.

## 6. QA Checkpoints to Prevent "ATS Drift"
- **The "No Requisition" Test:** Can a candidate be moved through a "Qualified" or "Screened" stage without being attached to a Job? (Must be YES for Agency).
- **The "Cross-Client" Test:** Can I see a candidate's submission history across multiple unrelated companies? (Must be YES for Agency).
- **The "Ownership" Test:** If Recruiter A adds a candidate, can Recruiter B take them without a Transfer of Ownership? (Must be NO).
