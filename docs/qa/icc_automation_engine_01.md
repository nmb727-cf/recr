# ICC Automation Engine 01

Date: 2026-04-01
Module ID: `ICC-AUTOMATION-ENGINE-01`

## Placement

Validated under:

- `Interview Command Center -> Automation`
- direct route remains available at `/interviews/automation`

## Implemented

- Automation types
  - Auto Scheduling
  - Auto Routing
  - Auto Decision
  - Auto Stage Movement
  - Auto Interview Trigger
  - Auto Notification
- Rule list
  - search
  - edit
  - duplicate
  - archive
  - enable / disable
- Rule builder wizard
  - Setup
  - Conditions
  - Actions
  - Preview
- Trigger support
  - prequalification completed
  - interview completed
  - score submitted
  - decision made
  - candidate status change
- Condition support
  - score threshold
  - interview type
  - decision
  - stage
  - candidate status
- Action support
  - move to next stage
  - schedule next interview
  - assign interviewer
  - send notification
  - trigger AI interview
  - reject candidate
  - mark hire ready
- Trigger runner
  - executes rules through the live automation trigger API
- Activity panel
  - shows recent automation logs when available

## Integration

Automation UI is aligned to:

- Flow Engine
- Scheduling Engine
- Interview Engines
- Decision Engine
- Notification workflows through action configuration

## Validation

Checked:

- automation section visible in Interview Command Center
- rule list loads
- create flow opens wizard
- edit flow opens wizard
- duplicate works through rule create API
- enable / disable works through update API
- trigger runner executes against automation trigger API
- no route conflict introduced
- no console-blocking build error

## Notes

- Action execution depends on the existing backend automation handlers for each trigger and action pair.
- The UI now exposes enterprise rule design clearly even when some downstream automations are still backend-policy dependent.

## Build Result

- `npx vite build` passed
