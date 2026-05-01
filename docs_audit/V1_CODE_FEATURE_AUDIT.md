# V1_CODE_FEATURE_AUDIT.md

## Executive Summary
This audit provides a comprehensive inventory of the V1 project features. The system is a multi-tenant Enterprise Recruitment Platform (SaaS) supporting three primary actors: Companies, Agencies, and Candidates. It features a sophisticated automation engine, deep candidate protection logic for agency-client relationships, a multi-round interview system with AI integration, and extensive analytics via an "Intelligence Substrate".

## Backend App Map
The backend is built with Django and follows a highly modular application structure.

| App | Key Models | Primary Viewsets/APIs | Actor | Status |
|-----|------------|-----------------------|-------|--------|
| `accounts` | `CustomUser`, `Role`, `Profile` | Auth, Profile, Team Management | All | Complete |
| `organisations` | `Organisation`, `Department`, `Location`, `Team` | Organisation Config, Hierarchy | Company | Complete |
| `agencies` | `AgencyClientRelationship`, `AgencyJobAssignment`, `GuestPortal` | Relationship Management, Job Assignments | Company/Agency | Complete |
| `jobs` | `JobRequisition`, `JobPosting`, `JobStage`, `JDTemplate` | Requisition Management, Public Jobs | Company | Complete |
| `candidates` | `Candidate`, `CandidateProfile`, `CandidateTenantRight` | Candidate DB, Protection Logic | All | Complete |
| `pipeline` | `Application`, `Placement`, `CommissionRecord` | Hiring Pipeline, Placements | All | Complete |
| `interviews` | `Interview`, `InterviewTemplate`, `ScorecardTemplate`, `QuestionBank` | Interview Management, Feedback, AI/Human rounds | All | Complete |
| `automation` | `AutomationRule`, `AutomationLog` | Event-Triggered Automation | Platform | Complete |
| `automation_sla` | `WorkflowSLAPolicy`, `WorkflowSLAExecution` | SLA Monitoring & Escalation | Platform | Complete |
| `automation_tasks` | `WorkflowTaskRule`, `WorkflowTaskExecution` | Automated Task Generation | Platform | Complete |
| `documents` | `Document`, `OfferLetter` | Document Vault, Offer Management | All | Complete |
| `analytics` | `SystemIntelligenceMemory` | Dashboards, Intelligence Projections | All | Complete |
| `passport` | `CandidatePassport` | Candidate-owned identity/resume share | Candidate | Partial |
| `rbac` | `Role`, `Permission`, `Resource` | Granular Access Control | Admin | Complete |
| `tenants` | `Tenant`, `Domain` | Multi-tenancy Management | Admin | Complete |

## Frontend Route/Page Map
The frontend uses React with Ant Design and React Router.

| Route | Page Component | Actor | Description |
|-------|----------------|-------|-------------|
| `/dashboard` | `Dashboard` | All | Unified dashboard with metrics |
| `/hiring-command-center` | `HiringCommandCenter` | Company | High-level hiring overview |
| `/jobs` | `JobsList` | Company | Requisition management |
| `/jobs/create` | `JobSetupStudio` | Company | Complex job creation wizard |
| `/candidates/database` | `CandidateDatabase` | All | Searchable candidate repository |
| `/pipeline` | `PipelineBoard` | All | Kanban view of applications |
| `/interviews` | `InterviewCommandCenter` | All | Unified interview management |
| `/interviews/ai` | `InterviewAIEngine` | All | AI interview configuration |
| `/offers` | `OfferManagement` | Company | Offer creation and tracking |
| `/agency/my-jobs` | `MyJobs` | Agency | Jobs assigned to the agency |
| `/agency/submit-candidate` | `SubmitCandidate` | Agency | Submission flow for agencies |
| `/candidate/passport` | `PassportPage` | Candidate | Candidate profile and share controls |
| `/admin/tenants` | `MasterAdminTenants` | Admin | Multi-tenant administration |

## Feature Inventory by Actor

### Company features
- **Requisition Management**: Complex approval chains, SLA tracking, hiring team configuration.
- **Agency Management**: Inviting agencies, setting tiers, managing contracts and commission.
- **Hiring Command Center**: Real-time intelligence on pipeline health and recruiter productivity.
- **Interview Center**: Configuring scorecards, scheduling (Google/Outlook), conducting live/AI interviews.
- **Offer Engine**: Multi-version offer letters, approval flows, negotiation tracking.

### Agency features
- **Client Relationship Management**: Managing multiple client (Company) connections, guest portal access for non-platform clients.
- **Submission Engine**: Submitting candidates to specific jobs with ownership protection.
- **Performance Analytics**: Tracking submission-to-hire ratios, SLA compliance.
- **Internal Database**: Agency-specific candidate pool and hotlists.

### Candidate features
- **Talent Passport**: Profile ownership, secure document vault, sharing/revoking access to recruiters.
- **Application Tracking**: Real-time status updates on all applications.
- **Interview Experience**: Self-scheduling, conducting AI/Video interviews, feedback tracking.

### Admin/platform features
- **Tenant Management**: Provisioning organisations and agencies, domain mapping.
- **Global Search**: Cross-tenant indexing for master admins.
- **Automation OS**: Designing system-wide playbooks for candidate nurturing and SLA enforcement.

## Company–Agency Relationship & Contract Findings
- **File**: `backend/apps/agencies/models.py` (`AgencyClientRelationship`)
- **Retention Logic**: Sophisticated protection system with configurable days (e.g., 90 days), start triggers (submission, rejection, last activity), and post-expiry modes (shared, company_use).
- **Commercials**: Fixed fee, percentage of salary, milestone-based payments.
- **Replacement Guarantee**: Automated tracking of guarantee periods (joining + X days).
- **Guest Portals**: Secure links for external clients to review submissions without full accounts.
- **Email Tracking**: Domain-based monitoring to claim ownership of candidate interactions.

## Job System Findings
- **File**: `backend/apps/jobs/models.py` (`JobRequisition`)
- **Workflow Modes**: Manual, Semi-Automated, Fully Automated.
- **Sourcing Governance**: Control over direct vs. agency submissions per job.
- **JD Templates**: Reusable library with category-based suggestions.
- **Stage Triggers**: Automated actions on stage entry (e.g., auto-schedule AI interview on 'Shortlisted').

## Candidate / CRM / Passport Findings
- **File**: `backend/apps/candidates/models.py`, `backend/apps/candidates/protection.py`
- **Identity Service**: `global_hash` used to track the same person across different tenants.
- **Protection Engine**: Rigorous enforcement of agency ownership; blocks companies from "stealing" agency candidates during the retention period.
- **Next Action System**: CRM-style follow-ups (Call, Email, WhatsApp) with due dates and owners.
- **Passport**: Candidate-centric model allowing controlled data sharing via `CandidateTenantRight`.

## Interview / Assessment Findings
- **File**: `backend/apps/interviews/models.py`
- **Execution Modes**: Native (AI/Video), Third-Party (Zoom/Teams), External Manual.
- **Scorecards**: Attribute-level weighting and scoring (1-5, Pass/Fail).
- **Question Bank**: Rich library including Coding, Video, and MCQ with difficulty levels.
- **Scheduling Engine**: Syncs with Google/Outlook, handles interviewer availability profiles and buffer times.

## Automation / Event Findings
- **File**: `backend/apps/automation/models.py`
- **Event Bus**: Triggers on `application.stage_changed`, `interview.completed`, `deadline.overdue`, etc.
- **SLA Policy**: Per-stage target hours with escalation rules to notify managers on breach.
- **Playbooks**: Complex action sequences (e.g., send email -> wait 2 days -> if no reply, move stage).

## Document / Offer / Placement Findings
- **File**: `backend/apps/documents/models.py`, `backend/apps/pipeline/models.py`
- **Offer Versioning**: Tracks multiple iterations of an offer.
- **Placement Tracking**: Records joins, tracks guarantee periods, and calculates agency commission.

## Analytics Findings
- **File**: `backend/apps/analytics/intelligence_substrate.py`
- **Intelligence Projections**: Real-time calculation of "Speed", "Success Rate", and "Best Role" for entities.
- **Funnel Analytics**: Stage-by-stage conversion rates with department/location filtering.

## Reusable Logic Map
- **Logic**: Candidate Protection & Retention (`backend/apps/candidates/protection.py`).
- **Logic**: Identity Matching & Global Hash (`backend/apps/candidates/models.py`).
- **Logic**: Intelligence Aggregation (`backend/apps/analytics/intelligence_substrate.py`).
- **Logic**: SLA Escalation Engine (`backend/apps/automation_sla/`).
- **Logic**: Reference ID Generation (`backend/apps/tenants/reference_ids.py`).

## Must Not Reuse / Broken Structure Map
- **Structure**: Gigantic `App.tsx` in frontend. (Discard: route everything properly in v4).
- **Structure**: Overly nested `automation_*` apps. (Refactor: consolidate into a cleaner workflow engine).
- **Structure**: Mixed business logic in Views. (Refactor: enforce Service layer in v4).

## Missing Compared to Enterprise Competitors
- **Multi-lingual Support**: Present in code but UI coverage is partial.
- **Advanced Workforce Planning**: No budgeting/forecasting module.
- **Vendor Management System (VMS)**: While agency features are strong, a full VMS for temporary labor is missing.
- **DEI Analytics**: Missing explicit diversity tracking/blind hiring features.

## Recommended V4 Migration/Reuse Strategy
1. **Extract Core Services**: Move the protection engine, identity service, and intelligence substrate into a "Core Platform" layer.
2. **Rewrite Frontend**: Move from a monolithic `App.tsx` to a modular, feature-based architecture (e.g., Nx or similar).
3. **Consolidate Automation**: Merge the various `automation_*` stubs into a single, unified "Workflow Engine" that uses a standard graph-based execution model.
4. **Refactor Interoperability**: Ensure the Candidate Passport is a standalone service that all other modules consume via a strict API.

---
*Audit completed on April 26, 2026.*
