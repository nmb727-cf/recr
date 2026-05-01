# QA Test Plan: Job-Interview Binding Completion (JOBS-PHASE-2-INTERVIEW)

## Overview
This document outlines the test cases for verifying the completion of Phase 2 Jobs: Interview Binding. The goal is to ensure that jobs can correctly bind to interview packages, customize rounds at the job level, and that automation/pipeline integration works as expected.

## STEP 1: UI Verification (Job Setup Studio)
1. **Package Selection**:
   - Create or Edit a Job.
   - Navigate to Step 6: Interview Configuration.
   - Verify that selecting an Interview Package initializes the rounds list correctly.
2. **Round Customization**:
   - Click on a round to expand it.
   - Verify that Round Name, Interview Type, and Question Template can be changed.
   - Verify that Pass Threshold (%) can be modified.
   - Toggle Auto-Pass, Auto-Reject, and Manual Review for a specific round.
   - Save the job and re-open to verify that overrides are persisted.
3. **Global Toggles**:
   - Verify that "Global Auto-Advance on Pass" and "Global Auto-Reject on Fail" toggles work and are saved.

## STEP 2: Job Command Center Verification
1. **Snapshot Data**:
   - Navigate to the Job Command Center for a job with a bound interview package.
   - Verify the "Interview Automation" widget shows:
     - Correct Active Package Name.
     - Automation Status (Active/Manual).
     - "In Interview" count (matches candidates in the 'interview' stage).
     - "Pending" count (matches scheduled but not completed interviews).
     - Preview of the first 3 rounds with their thresholds and auto-pass icons.
2. **Automation Toggle**:
   - Toggle the "Interview Automation" switch in the widget.
   - Verify it updates the binding status in the backend and reflects in the UI.

## STEP 3: Pipeline & Automation Integration (Backend)
1. **Auto-Advance (Next Round)**:
   - Move a candidate to the 'Interview' stage.
   - Complete the first interview with a score above the threshold.
   - Record a 'next_round' decision.
   - Verify that the next round interview is automatically created (if auto_pass is enabled).
2. **Auto-Reject**:
   - Record a 'reject' decision for an interview.
   - Verify that the Application status changes to 'rejected' automatically (if auto_reject is enabled).
3. **Manual Review**:
   - Enable 'Manual Review Required' for a round.
   - Complete the interview with a high score.
   - Verify that no automatic decision/next round is triggered, requiring a human to record the decision first.
4. **Threshold Logic**:
   - Verify that the AI evaluation (if used) correctly suggests 'next_round' or 'reject' based on the job-level threshold overrides, not just the package defaults.

## STEP 4: API Verification
1. **GET `/jobs/requisitions/{job_id}/interview-snapshot/`**:
   - Verify it returns correct aggregate data for the job.
2. **PUT `/jobs/requisitions/{job_id}/interview-binding/`**:
   - Verify `rounds_override` payload is accepted and persisted.
