# QA Document: Job Setup Studio (Full-Page Wizard)

## 1. Feature Overview
The Job Setup Studio is a comprehensive, full-page wizard that replaces the previous drawer-based job creation/editing form. It provides an enterprise-grade setup experience for recruitment requisitions, supporting the full architectural layers of the platform (Sourcing, Workflow, Interviews, Automation, SLA).

## 2. Why Drawer Form Was Replaced
- **Complexity**: The Job model now includes multiple layers (Interview Packages, Automation rules, Agency assignments) that exceeded the physical space of a drawer.
- **Field Parity**: The Information step has been fully aligned with the original form and backend schema, ensuring no data loss during the transition from drawer to wizard.
- **Clarity**: Step-based navigation provides better focus and logical progression for recruiters.
- **Intelligence**: Full-page layout allows for a persistent "Live Summary" and "Studio Intelligence" rail to guide the user.

## 3. Wizard Structure (Steps)
1. **Basic Job Info**: Title, Department, Location, Type, Work Mode, Experience Range, Salary, Confidentiality, Budget Code.
2. **Hiring Team**: Owner, Hiring Manager, and assigned Recruiters.
3. **Sourcing**: Internal/Hybrid/External modes and Agency assignments.
4. **Workflow**: Pipeline stage flow visualization.
5. **Interviews**: Binding Interview Packages and round threshold logic.
6. **Automation**: Toggling the Hiring AI Brain and decision engine triggers.
7. **Offers**: Foundation setup for final-stage commercials.
8. **Review**: Final configuration summary and launch trigger.

## 4. Information Step Field Mapping
The Information step ensures 100% parity with the original job system:
- **Core Identity**: title, department_id, location.
- **Hiring Parameters**: job_type, work_mode, headcount, priority, target_date, is_confidential, budget_code.
- **Experience & Compensation**: experience_min, experience_max, salary_min, salary_max, salary_currency, salary_visible.
- **Role Definition**: description, responsibilities, requirements, skills_required (tags).

## 5. UI Entry Points
- **Jobs List**: "Add Job" button navigates to `/jobs/create`.
- **Job Operational Card**: "Edit Setup" action navigates to `/jobs/:id/setup`.
- **Header Navigation**: "Jobs" dropdown menu includes "All Jobs" and "Create Job".
- **User Menu**: "Create Job" shortcut added.

## 6. Feature Integration
- **Interview Engine**: Directly binds packages during Step 5.
- **Agency Engine**: Assigns agencies during Step 3.
- **Automation Engine**: Controls global job automation toggles in Step 6.
- **SLA Engine**: References ownership and deadlines set during Team and Workflow steps.

## 7. Use Cases
- **Enterprise Requisition**: A Lead Recruiter starts a high-priority engineering role, configures standard rounds, assigns Tier 1 agencies, and enables AI Brain for automated screening.
- **Confidential Role**: Recruiter marks job as "Confidential" in Step 1 to redact details on public boards.
- **Compensation Focus**: Hiring Manager sets salary visibility to "Show on job boards" to increase applicant flow.

## 8. Validation Behavior
- **Step Validation**: "Save & Continue" triggers field validation for the active step.
- **Data Integrity**: Fields are mapped to top-level schema or metadata according to backend expectations.
- **Overall Progress**: Real-time progress bar reflects setup completeness.

## 9. Test Scenarios
- **Scenario 1: Complete Creation Flow**
    - Action: Navigate to `/jobs/create`, fill all 8 steps, and click "Publish".
    - Expected: Job created with all fields (including experience and skills) correctly saved.
- **Scenario 2: Experience Range Validation**
    - Action: In Step 1, enter experience range and verify it persists on save.
- **Scenario 3: Confidentiality redaction**
    - Action: Mark job as confidential.
    - Expected: Flag is saved; backend redaction logic (in serializer) is triggered.
- **Scenario 4: Edit Navigation**
    - Action: Click "Edit Setup" from an existing job card.
    - Expected: Studio initializes with ALL existing data pre-filled in all steps.
