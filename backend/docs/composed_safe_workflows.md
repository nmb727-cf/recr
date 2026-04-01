# Composed Safe Workflows

## Scheduled Follow-Up Escalation

Safest proven composed workflow:

1. Trigger event enters orchestration.
2. Orchestration creates an owner-owned deadline through the Pipeline contract.
3. Orchestration schedules a delayed communication follow-up through `schedule_followup`.
4. The scheduled follow-up executes later through the Communication owner contract.
5. A delayed escalation action executes later through the Pipeline escalation contract and Communication notification contract.
6. Scheduled-step failures remain non-blocking and are recorded both on the scheduled action row and in `action_results_json`.

### Owner contracts used

- `PipelineDeadlineService.create_from_orchestration(...)`
- `CommunicationDispatchService.enqueue_email_from_orchestration(...)`
- `PipelineDeadlineService.escalate_from_orchestration(...)`
- `CommunicationDispatchService.notify_from_orchestration(...)`

### Reusable orchestration pattern

- Keep orchestration as the coordinator only.
- Use immediate owner contracts for durable state such as deadlines.
- Use `schedule_followup` only to create dedupe-safe scheduled downstream actions.
- Let scheduled downstream actions call the same hardened owner contracts as immediate actions.
- Persist scheduled failure visibility in both `AutomationScheduledAction` and `AutomationExecutionRun.action_results_json`.

## Candidate Follow-Up With Escalation

Safest candidate-focused composed workflow:

1. Candidate event triggers orchestration.
2. Pipeline creates a candidate follow-up deadline.
3. Orchestration schedules a delayed candidate follow-up email.
4. If still unresolved, orchestration executes delayed escalation.
5. Pipeline remains owner of the deadline state and Communications remains owner of the email queue and escalation notification.

### Owner contracts used

- `PipelineDeadlineService.create_from_orchestration(...)`
- `CommunicationDispatchService.enqueue_email_from_orchestration(...)`
- `PipelineDeadlineService.escalate_from_orchestration(...)`
- `CommunicationDispatchService.notify_from_orchestration(...)`

### Safety boundary

- No candidate lifecycle mutation
- No direct orchestration writes to candidate state
- Duplicate suppression stays tenant-scoped
- Scheduled communication failure remains non-blocking while escalation still executes and is audited

## Agency Submission Feedback Follow-Up

Safest agency-submission workflow:

1. Agency submission enters the pipeline as an `application.created` event with `application.is_agency_submission = true`.
2. Pipeline creates a 24-48h feedback deadline on the application.
3. Orchestration schedules a delayed feedback reminder email to the client or an internal recruiter using Communication ownership.
4. If feedback is still unresolved, orchestration executes delayed escalation and notifies the recruiter or manager.

### Owner contracts used

- `PipelineDeadlineService.create_from_orchestration(...)`
- `CommunicationDispatchService.enqueue_email_from_orchestration(...)`
- `PipelineDeadlineService.escalate_from_orchestration(...)`
- `CommunicationDispatchService.notify_from_orchestration(...)`

### Safety boundary

- No application lifecycle mutation
- No direct orchestration writes to submission or agency records
- Duplicate suppression remains tenant-scoped for deadlines, scheduled reminders, and escalation notifications
- Scheduled reminder failure remains non-blocking while escalation still completes and is audited
