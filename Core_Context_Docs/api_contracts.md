# API Contracts — Recruitment Platform
# Research Date: March 2026
# Note: Billing and subscription endpoints excluded — added later

## Document Purpose
Complete API endpoint reference for all platform modules.
All agents must follow these contracts exactly.
Never create endpoints that deviate from these patterns.
Billing endpoints placeholder noted at bottom — implement later.

---

## API STANDARDS

### Base URL
All endpoints: /api/v1/

### Authentication
All endpoints require JWT token in header except public endpoints.
Header: Authorization: Bearer {access_token}

### Standard Response Format
Success:
{
  "success": true,
  "data": {},
  "message": "Human readable message",
  "meta": {
    "cursor": "next_cursor_value",
    "has_next": true,
    "total": 1000
  }
}

Error:
{
  "success": false,
  "data": null,
  "message": "Human readable error",
  "errors": {
    "field_name": ["error message"]
  }
}

### HTTP Status Codes
200 OK: Successful GET, PUT, PATCH
201 Created: Successful POST
204 No Content: Successful DELETE
400 Bad Request: Validation error
401 Unauthorized: Missing or invalid token
403 Forbidden: Valid token but no permission
404 Not Found: Resource does not exist
409 Conflict: Duplicate resource
429 Too Many Requests: Rate limit exceeded
500 Internal Server Error: Server error

### Pagination
All list endpoints use cursor-based pagination.
Query params: ?cursor=xxx&limit=20
Default limit: 20, Max limit: 100

### Filtering
Query params follow Django-filter conventions:
?status=active
?created_at__gte=2026-01-01
?search=john

### Sorting
?ordering=-created_at (descending)
?ordering=first_name (ascending)

---

## MODULE 1: AUTHENTICATION

### Public Endpoints (No auth required)

POST /api/v1/auth/register/company/
Register a new company tenant.
Body: {name, email, password, company_name, country_code}
Response: {user, tenant, access_token, refresh_token}

POST /api/v1/auth/register/agency/
Register a new agency tenant.
Body: {name, email, password, agency_name, country_code}
Response: {user, tenant, access_token, refresh_token}

POST /api/v1/auth/register/candidate/
Register a new candidate user.
Body: {first_name, last_name, email, password}
Response: {user, access_token, refresh_token}

POST /api/v1/auth/login/
Login for all user types.
Body: {email, password, tenant_slug (optional)}
Response: {user, tenant, access_token, refresh_token}

POST /api/v1/auth/refresh/
Refresh access token.
Body: {refresh_token}
Response: {access_token, refresh_token}

POST /api/v1/auth/forgot-password/
Body: {email}
Response: {message}

POST /api/v1/auth/reset-password/
Body: {token, new_password}
Response: {message}

POST /api/v1/auth/verify-email/
Body: {token}
Response: {message}

### Authenticated Endpoints

POST /api/v1/auth/logout/
Revoke refresh token.
Body: {refresh_token}
Response: {message}

GET /api/v1/auth/me/
Get current user profile.
Response: {user, tenant, permissions}

PUT /api/v1/auth/me/
Update current user profile.
Body: {first_name, last_name, phone, avatar_url, preferences}
Response: {user}

POST /api/v1/auth/change-password/
Body: {current_password, new_password}
Response: {message}

POST /api/v1/auth/mfa/enable/
Enable MFA for current user.
Response: {qr_code, secret}

POST /api/v1/auth/mfa/verify/
Body: {code}
Response: {message}

---

## MODULE 2: ORGANISATION MANAGEMENT

### Tenant Management

GET /api/v1/organisation/profile/
Get current tenant profile.
Response: {tenant}

PUT /api/v1/organisation/profile/
Update tenant profile.
Body: {name, website, logo_url, industry, size_range, settings, reference_prefix_custom}
Response: {tenant}

Organisation profile response includes:
* reference_prefix_auto
* reference_prefix_custom
* effective_reference_prefix

### Users

GET /api/v1/organisation/users/
List all users in tenant.
Query: ?role=recruiter&status=active&search=john
Response: {users[]}

POST /api/v1/organisation/users/
Invite new user to tenant.
Body: {email, role, first_name, last_name, team_id, department_id}
Response: {user}

GET /api/v1/organisation/users/{id}/
Response: {user}

PUT /api/v1/organisation/users/{id}/
Body: {role, is_active, team_id, department_id}
Response: {user}

DELETE /api/v1/organisation/users/{id}/
Soft delete user.
Response: {message}

### Departments

GET /api/v1/organisation/departments/
Response: {departments[]}

POST /api/v1/organisation/departments/
Body: {name, parent_department_id, head_user_id, description}
Response: {department}

GET /api/v1/organisation/departments/{id}/
Response: {department}

PUT /api/v1/organisation/departments/{id}/
Response: {department}

DELETE /api/v1/organisation/departments/{id}/
Response: {message}

### Locations

GET /api/v1/organisation/locations/
Response: {locations[]}

POST /api/v1/organisation/locations/
Body: {name, address_line1, city, state, country, postal_code, is_headquarters}
Response: {location}

GET /api/v1/organisation/locations/{id}/
Response: {location}

PUT /api/v1/organisation/locations/{id}/
Response: {location}

DELETE /api/v1/organisation/locations/{id}/
Response: {message}

### Teams

GET /api/v1/organisation/teams/
Response: {teams[]}

POST /api/v1/organisation/teams/
Body: {name, department_id, location_id, team_lead_id}
Response: {team}

GET /api/v1/organisation/teams/{id}/
Response: {team}

PUT /api/v1/organisation/teams/{id}/
Response: {team}

DELETE /api/v1/organisation/teams/{id}/
Response: {message}

---

## MODULE 3: JOB MANAGEMENT

### Requisitions

GET /api/v1/jobs/requisitions/
List all job requisitions.
Query: ?status=active&department_id=xxx&search=engineer
Response: {requisitions[]}

POST /api/v1/jobs/requisitions/
Create new job requisition.
Body: {title, department_id, location_id, job_type, work_mode,
       experience_min, experience_max, salary_min, salary_max,
       headcount, priority, is_confidential, description,
       requirements, responsibilities, skills_required, target_date}
Response: {requisition}

GET /api/v1/jobs/requisitions/{id}/
Response: {requisition, stages, applications_count}

PUT /api/v1/jobs/requisitions/{id}/
Response: {requisition}

DELETE /api/v1/jobs/requisitions/{id}/
Soft delete.
Response: {message}

POST /api/v1/jobs/requisitions/{id}/submit-for-approval/
Submit requisition for approval.
Response: {requisition}

POST /api/v1/jobs/requisitions/{id}/approve/
Approve requisition (approver only).
Body: {notes}
Response: {requisition}

POST /api/v1/jobs/requisitions/{id}/reject/
Reject requisition (approver only).
Body: {reason}
Response: {requisition}

POST /api/v1/jobs/requisitions/{id}/publish/
Publish approved requisition as job posting.
Response: {requisition, posting}

POST /api/v1/jobs/requisitions/{id}/clone/
Clone existing requisition.
Response: {requisition}

### Job Postings

GET /api/v1/jobs/postings/
Response: {postings[]}

GET /api/v1/jobs/postings/{id}/
Response: {posting}

PUT /api/v1/jobs/postings/{id}/
Body: {title, description_html, expires_at, is_active}
Response: {posting}

POST /api/v1/jobs/postings/{id}/pause/
Response: {posting}

POST /api/v1/jobs/postings/{id}/close/
Response: {posting}

### Job Stages

GET /api/v1/jobs/requisitions/{id}/stages/
Response: {stages[]}

POST /api/v1/jobs/requisitions/{id}/stages/
Body: {name, stage_order, stage_type, action_deadline_hours}
Response: {stage}

PUT /api/v1/jobs/requisitions/{id}/stages/{stage_id}/
Response: {stage}

DELETE /api/v1/jobs/requisitions/{id}/stages/{stage_id}/
Response: {message}

POST /api/v1/jobs/requisitions/{id}/stages/reorder/
Body: {stage_ids[]}
Response: {stages[]}

---

## MODULE 4: CANDIDATE MANAGEMENT

### Candidates

GET /api/v1/candidates/
List candidates.
Query: ?search=john&skills=python&experience_min=3&source=linkedin
Response: {candidates[]}

POST /api/v1/candidates/
Create new candidate.
Body: {first_name, last_name, email, phone, current_title,
       current_company, experience_years, skills, source}
Response: {candidate}

GET /api/v1/candidates/{id}/
Response: {candidate, profile, notes, applications, interviews}

PUT /api/v1/candidates/{id}/
Response: {candidate}

DELETE /api/v1/candidates/{id}/
Soft delete.
Response: {message}

POST /api/v1/candidates/{id}/upload-cv/
Upload CV file.
Body: multipart/form-data {file}
Response: {document, parsed_data}

GET /api/v1/candidates/{id}/timeline/
Full activity timeline for candidate.
Response: {events[]}

POST /api/v1/candidates/import/
Bulk import candidates from CSV.
Body: multipart/form-data {file}
Response: {imported_count, skipped_count, errors[]}

POST /api/v1/candidates/import-from-passport/
Import from Talent Passport link.
Body: {passport_token}
Response: {candidate}

GET /api/v1/candidates/duplicates/
List detected duplicate candidates.
Response: {duplicate_groups[]}

POST /api/v1/candidates/merge/
Merge duplicate candidates.
Body: {primary_id, duplicate_ids[]}
Response: {candidate}

### Candidate Notes

GET /api/v1/candidates/{id}/notes/
Response: {notes[]}

POST /api/v1/candidates/{id}/notes/
Body: {note_text, note_type, is_private}
Response: {note}

PUT /api/v1/candidates/{id}/notes/{note_id}/
Response: {note}

DELETE /api/v1/candidates/{id}/notes/{note_id}/
Response: {message}

---

## MODULE 5: APPLICATIONS AND PIPELINE

### Applications

GET /api/v1/applications/
List applications.
Query: ?requisition_id=xxx&status=shortlisted&stage_id=xxx
Response: {applications[]}

POST /api/v1/applications/
Create application (submit candidate for job).
Body: {candidate_id, requisition_id, source, agency_id}
Response: {application}

GET /api/v1/applications/{id}/
Response: {application, candidate, stage_history, interviews, notes}

PUT /api/v1/applications/{id}/
Manual stage/status changes in company-visible stages are allowed only for the job owner.
Response: {application}

POST /api/v1/applications/{id}/move-stage/
Move candidate to different stage.
Body: {stage_id, notes}
Manual stage movement in company-visible stages is allowed only for the job owner.
System/approved-threshold automation is exempt.
Response: {application}

POST /api/v1/applications/{id}/shortlist/
Body: {notes}
Allowed only for the job owner in company-visible stages (manual actions).
Response: {application}

POST /api/v1/applications/{id}/reject/
Body: {reason, category, send_email}
Allowed only for the job owner in company-visible stages (manual actions).
Response: {application}

POST /api/v1/applications/{id}/withdraw/
Body: {reason}
Response: {application}

POST /api/v1/applications/{id}/make-offer/
Body: {offer_amount, currency, joining_date, compensation_details}
Allowed only for the job owner in company-visible stages (manual actions).
Response: {application, offer_letter}

### Pipeline View

GET /api/v1/pipeline/{requisition_id}/
Get kanban pipeline view for a job.
Response: {stages[], applications_by_stage{}}

POST /api/v1/pipeline/bulk-action/
Bulk move, reject, or shortlist candidates.
Body: {application_ids[], action, data{}}
Manual stage actions are owner-restricted per application in company-visible stages.
Response: {updated_count, results[]}

### Action Deadlines

GET /api/v1/deadlines/
List pending action deadlines for current user.
Query: ?status=pending&overdue=true
Response: {deadlines[]}

POST /api/v1/deadlines/{id}/complete/
Mark deadline as completed.
Response: {deadline}

GET /api/v1/deadlines/overdue/
List all overdue actions.
Response: {deadlines[]}

---

## MODULE 6: AGENCY MANAGEMENT

### Agency Relationships (Company Side)

GET /api/v1/agencies/
List empanelled agencies.
Response: {agencies[]}

POST /api/v1/agencies/invite/
Invite agency to platform.
Body: {agency_email, agency_name, notes}
Response: {relationship}

GET /api/v1/agencies/{id}/
Response: {agency, performance, active_jobs, submissions}

PUT /api/v1/agencies/{id}/
Body: {tier, sla_submission_hours, commission_percentage, notes}
Response: {relationship}

POST /api/v1/agencies/{id}/suspend/
Body: {reason}
Response: {relationship}

POST /api/v1/agencies/{id}/terminate/
Body: {reason}
Response: {relationship}

GET /api/v1/agencies/{id}/performance/
Agency performance scorecard.
Response: {scores, metrics, trends}

### Job Distribution to Agencies

POST /api/v1/agencies/distribute-job/
Distribute job to selected agencies.
Body: {requisition_id, agency_ids[], deadline, max_submissions}
Response: {assignments[]}

GET /api/v1/agencies/job-assignments/
List all job-agency assignments.
Response: {assignments[]}

PUT /api/v1/agencies/job-assignments/{id}/
Body: {status, deadline, max_submissions}
Response: {assignment}

### Agency Side (Agency viewing their jobs)

GET /api/v1/agency/my-jobs/
Jobs assigned to this agency.
Response: {assignments[]}

POST /api/v1/agency/submit-candidate/
Submit candidate for a job.
Body: {candidate_id, requisition_id, cover_note}
Response: {application}

GET /api/v1/agency/my-submissions/
All candidate submissions by this agency.
Response: {applications[]}

GET /api/v1/agency/my-clients/
List client companies.
Response: {relationships[]}

---

## MODULE 7: INTERVIEW MANAGEMENT

### Interview Templates

GET /api/v1/interviews/templates/
Response: {templates[]}

POST /api/v1/interviews/templates/
Body: {name, description, interview_type, duration_minutes,
       passing_threshold, auto_shortlist_above, auto_reject_below,
       anti_cheat_enabled, questions[]}
Response: {template}

GET /api/v1/interviews/templates/{id}/
Response: {template}

PUT /api/v1/interviews/templates/{id}/
Response: {template}

DELETE /api/v1/interviews/templates/{id}/
Response: {message}

### Interviews

GET /api/v1/interviews/
List interviews.
Query: ?application_id=xxx&status=scheduled&type=panel
Response: {interviews[]}

POST /api/v1/interviews/
Schedule interview.
Body: {application_id, template_id, interview_type, scheduled_at,
       panelist_ids[], interview_round}
Response: {interview}

GET /api/v1/interviews/{id}/
Response: {interview, candidate, panelists, questions, scores}

PUT /api/v1/interviews/{id}/
Response: {interview}

POST /api/v1/interviews/{id}/start/
Start interview session.
Response: {interview, interview_link}

POST /api/v1/interviews/{id}/complete/
Complete interview.
Body: {overall_score, recommendation, feedback_summary}
Response: {interview}

POST /api/v1/interviews/{id}/cancel/
Body: {reason}
Response: {interview}

POST /api/v1/interviews/{id}/reschedule/
Body: {scheduled_at, reason}
Response: {interview}

### Interview Feedback (Panelist)

POST /api/v1/interviews/{id}/feedback/
Submit interviewer feedback.
Body: {score, recommendation, feedback, question_scores[]}
Response: {feedback}

GET /api/v1/interviews/{id}/feedback/
Get all feedback for interview.
Response: {feedbacks[]}

### Candidate Interview (Taking interview)

GET /api/v1/candidate/interviews/
List candidate's scheduled interviews.
Response: {interviews[]}

POST /api/v1/candidate/interviews/{id}/start/
Candidate starts async interview.
Response: {interview, questions[]}

POST /api/v1/candidate/interviews/{id}/submit-answer/
Submit answer to question.
Body: {question_id, answer_text, video_url, audio_url, code}
Response: {answer}

POST /api/v1/candidate/interviews/{id}/complete/
Candidate completes interview.
Response: {interview}

---

## MODULE 8: TALENT PASSPORT

### Passport Management (Candidate)

GET /api/v1/passport/my-passport/
Get own passport.
Response: {passport}

PUT /api/v1/passport/my-passport/
Update passport.
Body: {visibility_settings, professional_details, skills, work_history}
Response: {passport}

GET /api/v1/passport/my-passport/access-log/
Who has accessed my passport.
Response: {access_logs[]}

POST /api/v1/passport/my-passport/revoke-access/
Revoke access from specific viewer.
Body: {tenant_id, reason}
Response: {revocation}

POST /api/v1/passport/my-passport/revoke-all/
Revoke all access.
Response: {message}

GET /api/v1/passport/my-passport/share-link/
Get shareable passport link.
Response: {share_url, token}

POST /api/v1/passport/my-passport/regenerate-link/
Generate new share link (invalidates old).
Response: {share_url, token}

### Public Passport (No auth required)

GET /api/v1/passport/public/{token}/
View public passport page.
Response: {passport_public_data}

### Passport Import (Company and Agency)

POST /api/v1/passport/import/
Import candidate from passport link.
Body: {passport_token}
Response: {candidate, import_status}

---

## MODULE 9: INTERVIEW CAFE

### Session Management (Company)

GET /api/v1/cafe/sessions/
List cafe sessions.
Response: {sessions[]}

POST /api/v1/cafe/sessions/
Create new cafe session.
Body: {title, description, scheduled_start, scheduled_end,
       max_candidates, industries[], roles[], is_public}
Response: {session}

GET /api/v1/cafe/sessions/{id}/
Response: {session, booths[], registrations_count}

PUT /api/v1/cafe/sessions/{id}/
Response: {session}

POST /api/v1/cafe/sessions/{id}/start/
Start live cafe session.
Response: {session}

POST /api/v1/cafe/sessions/{id}/end/
End cafe session.
Response: {session, summary}

### Company Booth

GET /api/v1/cafe/sessions/{id}/booth/
Get my company booth for this session.
Response: {booth}

POST /api/v1/cafe/sessions/{id}/booth/
Set up company booth.
Body: {booth_name, description, available_positions[], hr_users[], max_interviews}
Response: {booth}

PUT /api/v1/cafe/sessions/{id}/booth/
Response: {booth}

### Interview Queue (POS Mission Control)

GET /api/v1/cafe/sessions/{id}/queue/
Get live interview queue.
Response: {queue[]}

POST /api/v1/cafe/sessions/{id}/queue/screen/
Screen candidate (shortlist or reject).
Body: {candidate_id, result, notes}
Response: {queue_entry}

POST /api/v1/cafe/sessions/{id}/queue/call-next/
Call next candidate for interview.
Response: {queue_entry, candidate}

POST /api/v1/cafe/sessions/{id}/queue/{entry_id}/complete/
Mark interview complete.
Body: {result, notes}
Response: {queue_entry}

### Candidate Cafe

GET /api/v1/cafe/upcoming/
List upcoming cafe sessions for candidates.
Response: {sessions[]}

POST /api/v1/cafe/sessions/{id}/register/
Candidate registers for cafe.
Body: {interested_roles[]}
Response: {registration}

POST /api/v1/cafe/sessions/{id}/checkin/
Candidate checks in to live session.
Response: {registration, available_booths[]}

GET /api/v1/cafe/sessions/{id}/live-status/
Real-time status during session.
Response: {queue_position, estimated_wait, session_status}

---

## MODULE 10: JOB SEARCH (Candidate)

GET /api/v1/jobs/search/
Public job search.
Query: ?q=engineer&location=bangalore&work_mode=remote&experience=3
Response: {jobs[]}

GET /api/v1/jobs/{posting_id}/
Public job detail page.
Response: {posting, company_info}

POST /api/v1/jobs/{posting_id}/apply/
One-click apply using passport.
Body: {cover_note (optional)}
Response: {application}

GET /api/v1/candidate/applications/
Candidate's application tracking dashboard.
Response: {applications[], stages_visible[]}

GET /api/v1/candidate/applications/{id}/
Application detail with full status tracking.
Response: {application, stage_history[], next_steps}

GET /api/v1/candidate/recommended-jobs/
Jobs recommended based on passport profile.
Response: {jobs[]}

POST /api/v1/jobs/{posting_id}/save/
Save job for later.
Response: {message}

GET /api/v1/candidate/saved-jobs/
Response: {jobs[]}

---

## MODULE 11: COMMUNICATION

### Messages

GET /api/v1/messages/threads/
List message threads.
Response: {threads[]}

GET /api/v1/messages/threads/{thread_id}/
Get messages in thread.
Response: {messages[]}

POST /api/v1/messages/threads/
Start new message thread.
Body: {recipient_id, recipient_tenant_id, subject, message,
       related_entity_type, related_entity_id}
Response: {thread, message}

POST /api/v1/messages/threads/{thread_id}/reply/
Reply to thread.
Body: {message, attachments[]}
Response: {message}

### Notifications

GET /api/v1/notifications/
List notifications for current user.
Query: ?is_read=false
Response: {notifications[]}

POST /api/v1/notifications/{id}/read/
Mark notification as read.
Response: {notification}

POST /api/v1/notifications/read-all/
Mark all as read.
Response: {message}

### Email Templates

GET /api/v1/communication/templates/
Response: {templates[]}

POST /api/v1/communication/templates/
Body: {name, subject, body_html, template_type, variables[]}
Response: {template}

PUT /api/v1/communication/templates/{id}/
Response: {template}

DELETE /api/v1/communication/templates/{id}/
Response: {message}

---

## MODULE 12: DOCUMENTS

GET /api/v1/documents/
List documents.
Query: ?document_type=cv&related_entity_type=candidate
Response: {documents[]}

POST /api/v1/documents/upload/
Upload document.
Body: multipart/form-data {file, document_type, related_entity_type, related_entity_id}
Response: {document}

GET /api/v1/documents/{id}/
Response: {document}

GET /api/v1/documents/{id}/download/
Get download URL.
Response: {download_url, expires_at}

DELETE /api/v1/documents/{id}/
Soft delete.
Response: {message}

### Offer Letters

GET /api/v1/offers/
List offer letters.
Response: {offers[]}

POST /api/v1/offers/
Create offer letter.
Body: {application_id, title, joining_date, offered_salary, currency, compensation_details}
Response: {offer}

GET /api/v1/offers/{id}/
Response: {offer}

POST /api/v1/offers/{id}/send/
Send offer to candidate.
Response: {offer}

POST /api/v1/offers/{id}/approve/
Approve offer (approver only).
Response: {offer}

POST /api/v1/offers/{id}/revoke/
Body: {reason}
Response: {offer}

POST /api/v1/candidate/offers/{id}/accept/
Candidate accepts offer.
Response: {offer}

POST /api/v1/candidate/offers/{id}/reject/
Candidate rejects offer.
Body: {reason}
Response: {offer}

---

## MODULE 13: ANALYTICS

GET /api/v1/analytics/dashboard/
Get role-based dashboard metrics.
Response: {metrics{}, charts{}}

GET /api/v1/analytics/recruitment/
Recruitment funnel analytics.
Query: ?start_date=2026-01-01&end_date=2026-03-31&department_id=xxx
Response: {funnel{}, time_to_hire{}, source_effectiveness{}}

GET /api/v1/analytics/agencies/
Agency performance analytics.
Response: {agencies[], rankings[], trends{}}

GET /api/v1/analytics/pipeline/
Pipeline health report.
Response: {stages[], bottlenecks[], deadlines_overdue[]}

GET /api/v1/analytics/candidates/
Candidate source and quality analytics.
Response: {sources{}, quality_scores{}, trends{}}

GET /api/v1/analytics/interviews/
Interview analytics.
Response: {completion_rates{}, score_distributions{}, types{}}

GET /api/v1/analytics/cafe/
Interview Cafe analytics.
Response: {sessions[], hired_count, attendance_rates{}}

---

## MODULE 14: MASTER ADMIN

All endpoints require super_admin role.

### Tenant Management

GET /api/v1/admin/tenants/
List all tenants on platform.
Response: {tenants[]}

GET /api/v1/admin/tenants/{id}/
Response: {tenant, settings, users_count, usage{}}

PUT /api/v1/admin/tenants/{id}/
Response: {tenant}

POST /api/v1/admin/tenants/{id}/suspend/
Body: {reason}
Response: {tenant}

POST /api/v1/admin/tenants/{id}/verify/
Manually verify tenant (for enterprise HQ).
Response: {tenant}

POST /api/v1/admin/tenants/merge/
Merge branch tenant into master.
Body: {branch_tenant_id, master_tenant_id, notes}
Response: {tenant}

### Feature and Limit Management
This is where subscription limits will be managed later.

GET /api/v1/admin/tenant-settings/{tenant_id}/
Get tenant feature limits.
Response: {settings}

PUT /api/v1/admin/tenant-settings/{tenant_id}/
Update tenant limits and features.
Body: {max_users, max_jobs, max_candidates, features_enabled{}}
Response: {settings}

### Platform Settings

GET /api/v1/admin/platform-settings/
Response: {settings[]}

PUT /api/v1/admin/platform-settings/{key}/
Body: {value}
Response: {setting}

### User Management

GET /api/v1/admin/users/
List all users across platform.
Response: {users[]}

POST /api/v1/admin/users/{id}/impersonate/
Impersonate user for support.
Response: {access_token}

POST /api/v1/admin/users/{id}/deactivate/
Response: {user}

### Analytics

GET /api/v1/admin/analytics/platform/
Platform-wide usage and growth analytics.
Response: {metrics{}}

GET /api/v1/admin/analytics/tenants/
Per-tenant usage analytics.
Response: {tenants[]}

### Audit Logs

GET /api/v1/admin/audit-logs/
Search audit logs.
Query: ?tenant_id=xxx&user_id=xxx&action=update&table_name=candidates
Response: {logs[]}

---

## WEBSOCKET ENDPOINTS

### Connection
ws://api/v1/ws/?token={access_token}

### Events (Server to Client)

notification.new
{type: "notification.new", data: {notification{}}}

application.stage_changed
{type: "application.stage_changed", data: {application_id, new_stage, candidate_name}}

deadline.overdue
{type: "deadline.overdue", data: {deadline{}}}

cafe.queue_update
{type: "cafe.queue_update", data: {session_id, queue[]}}

cafe.candidate_called
{type: "cafe.candidate_called", data: {session_id, candidate_id, booth_id}}

message.new
{type: "message.new", data: {thread_id, message{}}}

interview.started
{type: "interview.started", data: {interview_id}}

offer.action
{type: "offer.action", data: {offer_id, action, candidate_name}}

### Events (Client to Server)

cafe.checkin
{type: "cafe.checkin", data: {session_id}}

interview.ready
{type: "interview.ready", data: {interview_id}}

---

## BILLING PLACEHOLDER
Billing and subscription endpoints not implemented yet.
Will be added as Module 14 in future phase.
All feature limits managed via:
PUT /api/v1/admin/tenant-settings/{tenant_id}/
Until billing module is built.

Future billing endpoints will include:
POST /api/v1/billing/subscribe/
GET /api/v1/billing/plans/
GET /api/v1/billing/usage/
POST /api/v1/billing/upgrade/
POST /api/v1/billing/cancel/
ENDOFFILE

---

## MODULE: CANDIDATE/JOB REFERENCE IDs

Candidate responses include:
* `candidate_ref_id` (immutable human-facing reference)

Job requisition responses include:
* `job_ref_id` (immutable human-facing reference)

Search support:
* Candidate list/database `search` matches `candidate_ref_id`
* Job requisition list `search` matches `job_ref_id` and title
