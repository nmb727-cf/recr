# TOS-IH-UI-WORKFLOW-003

## 1. Naming Alignment

Locked naming split:
- user-facing module: `Intelligence Hub`
- internal backend app: `orchestration_center`

Reason:
- avoids collision with existing `Interview Command Center`
- keeps product naming clean for operations users
- preserves backend architecture already approved and scaffolded

Verdict alignment with approved context:
- architecture remains orchestration-only
- business modules remain source-of-truth
- no critical business flow may depend on AI or automation success
- manual fallback remains mandatory

## 2. Screen Map

First-level sidebar module:
- `Intelligence Hub`

Sections under Intelligence Hub:
1. Overview
2. Automations
3. AI Actions
4. Prompt Studio
5. Models & Providers
6. Executions
7. Failures & Queue
8. Approvals
9. Connectors
10. Settings

This must appear as a top-level operational module, not under Settings.

## 3. UI Hierarchy

Global structure:
- left sidebar navigation
- page-level summary header
- dense table/list workspace
- right-side detail panel
- contextual top actions
- badge-heavy status visibility

Core layout pattern for most screens:
- left: searchable/filterable list
- right: detail panel with tabs
- top: summary cards + page actions

This keeps the module operational, not decorative or developer-only.

## 4. Overview Screen

Purpose:
- operational health and workload visibility for AI and automation across TOS

Top summary cards:
- AI Executions Today
- Automation Runs Today
- Failed Executions
- Pending Approvals
- Active Automations
- AI Health Status

Middle content:
- execution activity timeline
- recent AI actions
- automation runs
- failures
- approvals

Right rail:
- provider health
- queue status
- worker status
- model availability

Bottom section:
- recent issues
- retry-needed items
- pending-approval items
- degraded providers

UX decisions:
- dense but readable
- strong use of severity/status colors
- operational summaries first, raw logs second

## 5. Automations Screen

Purpose:
- manage tenant and platform automation rules safely

Primary layout:
- left: rules list
- right: rule details

Rules list columns:
- Name
- Module
- Trigger
- Status
- Last Run
- Next Run
- Owner
- Scope

Detail panel tabs:
- Conditions
- Actions
- Execution History
- Settings
- Audit

Top controls:
- Create Rule
- Toggle Enable
- Test Rule
- Pause Rule
- Duplicate Rule

Rule categories:
- system rules
- tenant rules
- built-in rules

Required interaction support:
- enable/disable
- pause/resume
- test
- simulate
- audit trail review

## 6. AI Actions Screen

Purpose:
- operational visibility and control over AI-assisted features by module

Grouped sections:

Candidates:
- resume parsing
- profile enrichment
- similarity search

Jobs:
- candidate matching
- job enrichment

Interviews:
- interview scoring
- transcript analysis
- summary generation

Communication:
- email drafting
- outreach generation

Pipeline:
- ranking suggestions
- stage recommendations

Each action card shows:
- status
- usage volume
- last execution
- enabled/disabled
- approval mode
- failure rate snippet

Right panel:
- action settings
- approval mode
- allowed providers
- fallback behavior
- routing summary

## 7. Prompt Studio

Purpose:
- central prompt management with governance and testing

Layout:
- left: prompt list
- right: prompt editor / inspector

Prompt list columns:
- Name
- Module
- Use Case
- Version
- Status
- Active

Detail/editor tabs:
- Prompt Content
- Variables
- Output Schema
- Test Console
- Version History
- Audit

Top controls:
- New Prompt
- New Version
- Test
- Approve
- Archive

Must support:
- draft safely
- compare versions
- preview output
- test before activation
- show active/approved separation clearly

## 8. Models & Providers Screen

Purpose:
- manage routing and provider health without exposing unnecessary low-level complexity

Left list:
- Provider Name
- Type
- Status
- Health
- Priority

Right detail tabs:
- Models
- Routing
- Timeout
- Retry
- Health
- Logs

Model view rows:
- model name
- capabilities
- enabled
- priority
- health

UX decision:
- show platform defaults and tenant overrides distinctly

## 9. Executions Screen

Purpose:
- inspect actual AI and automation execution history

Tabs:
- AI Executions
- Automation Runs

List columns:
- ID
- Module
- Entity
- Status
- Duration
- Provider
- Model
- Time

Right detail panel:
- request payload summary
- response / normalized output
- logs
- retry
- approve
- cancel

UX rule:
- raw payloads available but collapsed by default
- normalized output and failure explanation prioritized first

## 10. Failures & Queue Screen

Tabs:
- Failures
- Dead Letter
- Queue

Failure list columns:
- Type
- Module
- Reason
- Retryable
- Created

Right panel actions:
- Retry
- Ignore
- Requeue
- Add Notes

Queue view should surface:
- queued volume
- stuck runs
- scheduled items
- worker lag indicators

## 11. Approvals Screen

Purpose:
- human-in-loop review for AI outputs and restricted automations

Columns:
- Item Type
- Module
- Reason
- Requested By
- Time
- Status

Right panel actions:
- Approve
- Reject
- Comment

Important UX rule:
- always show why approval is required
- show source execution context without forcing user to leave screen

## 12. Connectors Screen

Purpose:
- visibility into which TOS modules are integrated with Intelligence Hub

Connector list:
- Candidates
- Jobs
- Pipeline
- Interviews
- Communication
- Passport
- HDC
- ICC
- Analytics

Each connector row shows:
- enabled
- AI enabled
- automation enabled
- fallback behavior
- event coverage
- compatibility status

## 13. Settings Screen

Tenant-level controls:
- AI enabled
- automation enabled
- approval defaults
- retry policy
- provider restrictions
- notification preferences
- feature toggles
- connector enablement

UX rule:
- split platform defaults from tenant overrides
- warn clearly before disabling shared intelligence capabilities

## 14. Workflow Examples

### Example 1: Candidate Created
- candidate created in Candidate module
- event emitted
- Intelligence Hub receives event
- resume parsing AI request created
- result saved if successful
- if failure occurs, candidate remains created and recruiter can continue manually

### Example 2: Interview Completed
- interview marked complete
- event emitted
- Intelligence Hub triggers interview summary/scoring
- output marked `approval_required` if configured
- recruiter or HR manager approves or rejects
- interview completion remains valid regardless

### Example 3: Application Stuck 48 Hours
- pipeline event or scheduled automation check detects inactivity
- matching rule finds applicable automation
- reminder or escalation created
- if automation fails, application remains unaffected and manual follow-up is still possible

## 15. Interaction Flows

### Prompt approval flow
1. admin opens Prompt Studio
2. selects prompt
3. creates or reviews version
4. tests output
5. submits for approval
6. approver reviews and activates

### Failed execution remediation flow
1. operator opens Failures & Queue
2. selects failed run
3. reviews reason and retry eligibility
4. retries or moves to dead-letter
5. adds operator note

### Approval-required AI output flow
1. approval appears in Approvals
2. reviewer opens detail
3. compares suggested output and source context
4. approves or rejects
5. audit entry recorded

## 16. Role Permissions In UI

### Platform Admin
Can:
- edit prompts
- approve prompts
- manage providers
- manage routing
- enable/disable automations
- retry executions
- resolve failures
- approve AI outputs
- manage tenant settings

### Tenant Admin
Can:
- manage tenant prompts if allowed
- enable/disable tenant automations
- retry tenant executions
- resolve tenant failures
- approve AI outputs where policy allows
- manage tenant intelligence settings

### HR Manager
Can:
- view overview
- view executions
- approve operational AI outputs if granted
- retry selected failures if allowed
- review automation history

### Recruiter
Can:
- view limited overview
- view relevant executions
- view AI action states
- request rerun where allowed
- cannot manage providers
- cannot activate prompts
- cannot enable high-risk automations

### Candidate
Can:
- no direct Intelligence Hub access

## 17. UX Decisions

Locked UX choices:
- first-level module visibility
- enterprise dense layout
- list + right-panel detail pattern
- badges and severity states emphasized
- operational wording over technical jargon
- manual/fallback actions always visible where relevant
- audit visibility built into every sensitive screen

## 18. Final Recommendation

Use this naming and UX split:
- UI/module name: `Intelligence Hub`
- backend app: `orchestration_center`

Rollout recommendation:
- add menu visibility only after overview, prompts, automations, executions, failures, approvals, and settings screens have at least shell-level completeness
- expose recruiter views as limited operational visibility
- keep provider/routing edits restricted to platform and tenant admins
- keep the module visibly operational, not hidden inside settings or admin-only tooling
