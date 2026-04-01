# ICC Scheduling Engine 03

Date: 2026-03-29
Module ID: `ICC-SCHEDULING-ENGINE-01`

## Placement

Validated under:

- `Interview Command Center -> Scheduling`

## What Was Implemented

- Added `Scheduling` as a first-class Interview Command Center section
- Rebuilt the scheduling workspace in `InterviewSchedulingEngine.tsx`
- Updated header CTA `Schedule Interview` to open Scheduling instead of Operations

## Scheduling Modes Covered

- Manual Scheduling
- System Availability Scheduling
- Calendar-Based Scheduling
- Candidate Self Scheduling

## Main UI Areas

- scheduling dashboard stats
- schedule interview workspace
- availability profile and blocked time
- panel/common slot finder
- optional calendar connection setup
- candidate self-scheduling link generation
- upcoming interviews list with reschedule and cancel actions

## Real Backend Integration

Connected to real APIs for:

- interview list
- manual scheduling
- availability profile
- availability blocks
- panel slot calculation
- scheduling link generation
- calendar connection config
- interview reschedule
- interview cancel

Also connected to existing ICC sources for:

- interview types
- templates
- flows
- candidates
- jobs
- applications

## Validation

Checked:

- Scheduling visible as separate ICC section
- manual scheduling form renders with candidate, type, template, stage, interviewer, date, time, duration, timezone, and mode
- system availability profile works
- blocked time creation works
- panel slot finder works
- candidate self-scheduling link shell works
- calendar-based config works without forcing a calendar dependency
- reschedule action works from upcoming interviews list
- cancel action works from upcoming interviews list
- no route conflict introduced
- no console-blocking build error

## Notes

- Calendar providers are treated as optional readiness/configuration, which matches the product requirement.
- Candidate self-scheduling is implemented as a real scheduling link flow for existing interviews.
- The scheduling form uses live application, candidate, requisition, type, and template data to avoid raw-ID-only UX.

## Build Result

- `npx vite build` passed
