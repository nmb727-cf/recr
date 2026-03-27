# Database Schema — Recruitment Platform
# Research Date: March 2026
# Based on: Independent research, ATS industry standards, PostgreSQL multi-tenancy best practices

## Document Purpose
Complete database schema for all platform modules.
All agents must follow this schema exactly.
Never create tables without referencing this document.
Billing and subscription excluded — will be added later via admin configuration.

---

## SCHEMA DESIGN PRINCIPLES

### Research-Backed Decisions
From Crunchy Data, Citus Docs, and Streamkap research:
- Shared schema with tenant_id on every table is the correct approach
- tenant_id is not bad design — it is the linchpin of multi-tenant strategy
- Every query must filter by tenant_id as first WHERE clause
- PostgreSQL RLS enforces this at database level as safety net
- UUID v7 primary keys for better B-tree index performance
- JSONB columns for flexible tenant-specific custom fields
- Soft delete on all tables — never hard delete

### Standard Columns on Every Table
Every single table in this database must have these columns:
- id UUID PRIMARY KEY DEFAULT gen_random_uuid()
- tenant_id UUID NOT NULL REFERENCES tenants(id)
- created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
- updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
- created_by UUID REFERENCES users(id)
- is_deleted BOOLEAN NOT NULL DEFAULT FALSE
- deleted_at TIMESTAMPTZ
- metadata JSONB DEFAULT '{}'

metadata JSONB column serves two purposes:
1. Tenant-specific custom fields without schema migration
2. Future extensibility for any table

---

## GROUP 1: PLATFORM AND TENANT MANAGEMENT
These tables are SHARED — no tenant_id, accessible platform-wide

### TABLE: tenants
Stores all companies, agencies on the platform.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_type VARCHAR(20) NOT NULL (company, agency, candidate_pool)
name VARCHAR(255) NOT NULL
slug VARCHAR(100) UNIQUE NOT NULL (used for subdomain routing)
master_id UUID REFERENCES tenants(id) (for enterprise HQ linking)
is_master BOOLEAN DEFAULT FALSE
status VARCHAR(20) DEFAULT 'active' (active, suspended, pending_verification)
verified_at TIMESTAMPTZ
verified_by UUID
country_code VARCHAR(5)
timezone VARCHAR(50) DEFAULT 'UTC'
logo_url TEXT
website VARCHAR(255)
industry VARCHAR(100)
size_range VARCHAR(50) (1-10, 11-50, 51-200, 201-500, 500+)
cin VARCHAR(50) (Company Identification Number for India)
registration_number VARCHAR(100)
custom_fields JSONB DEFAULT '{}'
settings JSONB DEFAULT '{}'
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ

### TABLE: users
All users across all tenant types.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
email VARCHAR(255) NOT NULL
email_verified BOOLEAN DEFAULT FALSE
phone VARCHAR(20)
phone_verified BOOLEAN DEFAULT FALSE
password_hash VARCHAR(255)
first_name VARCHAR(100)
last_name VARCHAR(100)
avatar_url TEXT
role VARCHAR(50) NOT NULL (super_admin, tenant_admin, recruiter, hr_manager,
hiring_manager, interviewer, candidate, agency_owner,
agency_recruiter, viewer)
is_active BOOLEAN DEFAULT TRUE
last_login_at TIMESTAMPTZ
last_login_ip VARCHAR(45)
mfa_enabled BOOLEAN DEFAULT FALSE
mfa_secret VARCHAR(255)
notification_preferences JSONB DEFAULT '{}'
ui_preferences JSONB DEFAULT '{}'
timezone VARCHAR(50) DEFAULT 'UTC'
language VARCHAR(10) DEFAULT 'en'
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'
UNIQUE(tenant_id, email)

### TABLE: user_sessions
JWT refresh token management.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id UUID NOT NULL REFERENCES users(id)
tenant_id UUID NOT NULL REFERENCES tenants(id)
refresh_token_hash VARCHAR(255) NOT NULL
ip_address VARCHAR(45)
user_agent TEXT
device_info JSONB DEFAULT '{}'
expires_at TIMESTAMPTZ NOT NULL
revoked_at TIMESTAMPTZ
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

### TABLE: audit_logs
Immutable record of every data change. Cannot be updated or deleted.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID REFERENCES tenants(id)
user_id UUID REFERENCES users(id)
action VARCHAR(50) NOT NULL (create, update, delete, login, logout, export, view)
table_name VARCHAR(100) NOT NULL
record_id UUID
old_values JSONB
new_values JSONB
ip_address VARCHAR(45)
user_agent TEXT
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

### TABLE: platform_settings
Master admin configuration for entire platform.
All subscription limits and feature flags stored here.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
key VARCHAR(255) UNIQUE NOT NULL
value JSONB NOT NULL
description TEXT
category VARCHAR(100)
is_public BOOLEAN DEFAULT FALSE
updated_by UUID REFERENCES users(id)
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

### TABLE: tenant_settings
Per-tenant configuration overrides.
This is where subscription limits will be enforced later.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id) UNIQUE
max_users INTEGER DEFAULT 999999
max_jobs INTEGER DEFAULT 999999
max_candidates INTEGER DEFAULT 999999
max_agencies INTEGER DEFAULT 999999
features_enabled JSONB DEFAULT '{}'
custom_config JSONB DEFAULT '{}'
notes TEXT
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

---

## GROUP 2: ORGANISATION MANAGEMENT

### TABLE: departments
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
name VARCHAR(255) NOT NULL
parent_department_id UUID REFERENCES departments(id)
head_user_id UUID REFERENCES users(id)
description TEXT
is_active BOOLEAN DEFAULT TRUE
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: locations
Branch and office locations for enterprises.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
name VARCHAR(255) NOT NULL
address_line1 VARCHAR(255)
address_line2 VARCHAR(255)
city VARCHAR(100)
state VARCHAR(100)
country VARCHAR(100)
postal_code VARCHAR(20)
latitude DECIMAL(10,8)
longitude DECIMAL(11,8)
is_headquarters BOOLEAN DEFAULT FALSE
is_active BOOLEAN DEFAULT TRUE
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: teams
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
name VARCHAR(255) NOT NULL
department_id UUID REFERENCES departments(id)
location_id UUID REFERENCES locations(id)
team_lead_id UUID REFERENCES users(id)
description TEXT
is_active BOOLEAN DEFAULT TRUE
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

---

## GROUP 3: JOB MANAGEMENT

### TABLE: job_requisitions
Job opening requests before approval.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
title VARCHAR(255) NOT NULL
department_id UUID REFERENCES departments(id)
location_id UUID REFERENCES locations(id)
job_type VARCHAR(50) (full_time, part_time, contract, internship, freelance)
work_mode VARCHAR(50) (onsite, remote, hybrid)
experience_min INTEGER
experience_max INTEGER
salary_min DECIMAL(15,2)
salary_max DECIMAL(15,2)
salary_currency VARCHAR(10) DEFAULT 'INR'
salary_visible BOOLEAN DEFAULT FALSE
headcount INTEGER DEFAULT 1
priority VARCHAR(20) DEFAULT 'medium' (low, medium, high, urgent)
is_confidential BOOLEAN DEFAULT FALSE
description TEXT
requirements TEXT
responsibilities TEXT
skills_required JSONB DEFAULT '[]'
status VARCHAR(50) DEFAULT 'draft'
(draft, pending_approval, approved, active, paused, closed, cancelled)
approval_chain JSONB DEFAULT '[]'
current_approver_id UUID REFERENCES users(id)
approved_at TIMESTAMPTZ
approved_by UUID REFERENCES users(id)
target_date DATE
closed_at TIMESTAMPTZ
closed_reason VARCHAR(255)
source VARCHAR(50) (internal, agency, direct, referral)
budget_code VARCHAR(100)
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID NOT NULL REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: job_postings
Published version of requisition for external visibility.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
requisition_id UUID NOT NULL REFERENCES job_requisitions(id)
title VARCHAR(255) NOT NULL
slug VARCHAR(255)
description_html TEXT
external_description TEXT
posted_at TIMESTAMPTZ
expires_at TIMESTAMPTZ
is_active BOOLEAN DEFAULT TRUE
views_count INTEGER DEFAULT 0
applications_count INTEGER DEFAULT 0
posted_on JSONB DEFAULT '[]' (list of job boards posted to)
custom_application_form JSONB DEFAULT '{}'
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: job_stages
Custom hiring pipeline stages per job.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
requisition_id UUID NOT NULL REFERENCES job_requisitions(id)
name VARCHAR(100) NOT NULL
stage_order INTEGER NOT NULL
stage_type VARCHAR(50)
(sourcing, screening, interview, assessment, offer, joined, rejected, withdrawn)
action_deadline_hours INTEGER DEFAULT 48
auto_actions JSONB DEFAULT '{}'
is_active BOOLEAN DEFAULT TRUE
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
metadata JSONB DEFAULT '{}'

---

## GROUP 4: CANDIDATE MANAGEMENT

### TABLE: candidates
Global candidate pool — shared across platform with tenant isolation.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
first_name VARCHAR(100) NOT NULL
last_name VARCHAR(100) NOT NULL
email VARCHAR(255)
phone VARCHAR(20)
whatsapp VARCHAR(20)
linkedin_url TEXT
current_title VARCHAR(255)
current_company VARCHAR(255)
current_location_city VARCHAR(100)
current_location_country VARCHAR(100)
experience_years DECIMAL(4,1)
expected_salary_min DECIMAL(15,2)
expected_salary_max DECIMAL(15,2)
salary_currency VARCHAR(10) DEFAULT 'INR'
notice_period_days INTEGER
availability_date DATE
is_actively_looking BOOLEAN DEFAULT TRUE
source VARCHAR(100)
source_detail TEXT
passport_id UUID REFERENCES talent_passports(id)
duplicate_of UUID REFERENCES candidates(id)
is_duplicate BOOLEAN DEFAULT FALSE
global_hash VARCHAR(64) (hash of email+phone for dedup detection)
tags JSONB DEFAULT '[]'
skills JSONB DEFAULT '[]'
languages JSONB DEFAULT '[]'
assigned_to UUID REFERENCES users(id)
owner_user_id UUID REFERENCES users(id)
owner_tenant_id UUID REFERENCES tenants(id)
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: candidate_profiles
Extended professional profile details.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
candidate_id UUID NOT NULL REFERENCES candidates(id)
summary TEXT
work_experience JSONB DEFAULT '[]'
education JSONB DEFAULT '[]'
certifications JSONB DEFAULT '[]'
projects JSONB DEFAULT '[]'
publications JSONB DEFAULT '[]'
awards JSONB DEFAULT '[]'
languages JSONB DEFAULT '[]'
references JSONB DEFAULT '[]'
cv_url TEXT
cv_parsed_data JSONB DEFAULT '{}'
cv_uploaded_at TIMESTAMPTZ
portfolio_url TEXT
github_url TEXT
stackoverflow_url TEXT
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: candidate_notes
Notes added by recruiters about candidates.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
candidate_id UUID NOT NULL REFERENCES candidates(id)
note_text TEXT NOT NULL
note_type VARCHAR(50) DEFAULT 'general'
(general, call_log, email_log, interview_note, warning, positive)
is_private BOOLEAN DEFAULT FALSE
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID NOT NULL REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: candidate_tags
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
name VARCHAR(100) NOT NULL
color VARCHAR(20)
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
UNIQUE(tenant_id, name)

---

## GROUP 5: APPLICATIONS AND PIPELINE

### TABLE: applications
Candidate applied or submitted for a specific job.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
candidate_id UUID NOT NULL REFERENCES candidates(id)
requisition_id UUID NOT NULL REFERENCES job_requisitions(id)
current_stage_id UUID REFERENCES job_stages(id)
status VARCHAR(50) DEFAULT 'applied'
(applied, screening, shortlisted, interview, assessment, offer,
joined, rejected, withdrawn, on_hold)
source VARCHAR(100)
source_detail TEXT
submitted_by UUID REFERENCES users(id)
submitted_by_tenant_id UUID REFERENCES tenants(id)
agency_id UUID REFERENCES tenants(id)
match_score DECIMAL(5,2)
is_agency_submission BOOLEAN DEFAULT FALSE
rejection_reason TEXT
rejection_category VARCHAR(100)
withdrawn_reason TEXT
offer_amount DECIMAL(15,2)
offer_currency VARCHAR(10)
offer_date DATE
offer_accepted_at TIMESTAMPTZ
offer_rejected_at TIMESTAMPTZ
joining_date DATE
joined_at TIMESTAMPTZ
application_form_data JSONB DEFAULT '{}'
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'
UNIQUE(tenant_id, candidate_id, requisition_id)

### TABLE: application_stage_history
Complete history of every stage movement.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
application_id UUID NOT NULL REFERENCES applications(id)
from_stage_id UUID REFERENCES job_stages(id)
to_stage_id UUID REFERENCES job_stages(id)
from_status VARCHAR(50)
to_status VARCHAR(50)
moved_by UUID REFERENCES users(id)
reason TEXT
notes TEXT
moved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
metadata JSONB DEFAULT '{}'

### TABLE: action_deadlines
The 24-48 hour trigger system.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
entity_type VARCHAR(50) NOT NULL (application, interview, offer, requisition)
entity_id UUID NOT NULL
action_required VARCHAR(255) NOT NULL
assigned_to UUID REFERENCES users(id)
escalate_to UUID REFERENCES users(id)
deadline_at TIMESTAMPTZ NOT NULL
reminder_sent_at TIMESTAMPTZ
escalated_at TIMESTAMPTZ
completed_at TIMESTAMPTZ
status VARCHAR(20) DEFAULT 'pending' (pending, reminded, escalated, completed, cancelled)
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
metadata JSONB DEFAULT '{}'

---

## GROUP 6: AGENCY AND VENDOR MANAGEMENT

### TABLE: agency_client_relationships
Agency to company relationships.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
agency_tenant_id UUID NOT NULL REFERENCES tenants(id)
company_tenant_id UUID NOT NULL REFERENCES tenants(id)
status VARCHAR(50) DEFAULT 'active'
(pending, active, suspended, terminated)
tier VARCHAR(50) DEFAULT 'standard' (preferred, standard, probation, blacklisted)
contract_start_date DATE
contract_end_date DATE
sla_submission_hours INTEGER DEFAULT 48
sla_feedback_hours INTEGER DEFAULT 72
commission_percentage DECIMAL(5,2)
commission_type VARCHAR(50) (percentage, fixed, milestone)
notes TEXT
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'
UNIQUE(agency_tenant_id, company_tenant_id)

### TABLE: agency_job_assignments
Which jobs are assigned to which agencies.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
requisition_id UUID NOT NULL REFERENCES job_requisitions(id)
agency_tenant_id UUID NOT NULL REFERENCES tenants(id)
assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
assigned_by UUID REFERENCES users(id)
deadline DATE
max_submissions INTEGER
submission_count INTEGER DEFAULT 0
status VARCHAR(50) DEFAULT 'active' (active, paused, closed)
notes TEXT
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
metadata JSONB DEFAULT '{}'
UNIQUE(requisition_id, agency_tenant_id)

### TABLE: agency_performance_scores
Calculated performance metrics per agency per company.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
agency_tenant_id UUID NOT NULL REFERENCES tenants(id)
company_tenant_id UUID NOT NULL REFERENCES tenants(id)
period_start DATE NOT NULL
period_end DATE NOT NULL
total_submissions INTEGER DEFAULT 0
shortlisted_count INTEGER DEFAULT 0
interviewed_count INTEGER DEFAULT 0
offered_count INTEGER DEFAULT 0
joined_count INTEGER DEFAULT 0
shortlist_rate DECIMAL(5,2)
offer_rate DECIMAL(5,2)
join_rate DECIMAL(5,2)
avg_submission_time_hours DECIMAL(8,2)
overall_score DECIMAL(5,2)
calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
metadata JSONB DEFAULT '{}'

---

## GROUP 7: INTERVIEW MANAGEMENT

### TABLE: interview_templates
Reusable interview designs.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
name VARCHAR(255) NOT NULL
description TEXT
interview_type VARCHAR(50) NOT NULL
(ai_screening, one_way_video, live_video, panel, technical,
group_discussion, psychometric, case_study, mock)
duration_minutes INTEGER
instructions TEXT
passing_threshold DECIMAL(5,2)
auto_shortlist_above DECIMAL(5,2)
auto_reject_below DECIMAL(5,2)
anti_cheat_enabled BOOLEAN DEFAULT TRUE
recording_enabled BOOLEAN DEFAULT TRUE
questions JSONB DEFAULT '[]'
scoring_criteria JSONB DEFAULT '{}'
is_active BOOLEAN DEFAULT TRUE
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: interviews
Scheduled or completed interview instances.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
application_id UUID NOT NULL REFERENCES applications(id)
candidate_id UUID NOT NULL REFERENCES candidates(id)
requisition_id UUID NOT NULL REFERENCES job_requisitions(id)
template_id UUID REFERENCES interview_templates(id)
interview_type VARCHAR(50) NOT NULL
interview_round INTEGER DEFAULT 1
title VARCHAR(255)
scheduled_at TIMESTAMPTZ
started_at TIMESTAMPTZ
completed_at TIMESTAMPTZ
duration_minutes INTEGER
status VARCHAR(50) DEFAULT 'scheduled'
(scheduled, in_progress, completed, cancelled, no_show, rescheduled)
interview_link TEXT
recording_url TEXT
overall_score DECIMAL(5,2)
ai_score DECIMAL(5,2)
human_score DECIMAL(5,2)
recommendation VARCHAR(50) (strongly_recommend, recommend, neutral, not_recommend, reject)
feedback_summary TEXT
anti_cheat_score DECIMAL(5,2)
anti_cheat_flags JSONB DEFAULT '[]'
is_cafe_interview BOOLEAN DEFAULT FALSE
cafe_session_id UUID REFERENCES cafe_sessions(id)
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: interview_panelists
Interviewers assigned to an interview.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
interview_id UUID NOT NULL REFERENCES interviews(id)
interviewer_id UUID NOT NULL REFERENCES users(id)
role VARCHAR(50) DEFAULT 'interviewer' (lead, interviewer, observer)
score DECIMAL(5,2)
feedback TEXT
recommendation VARCHAR(50)
submitted_at TIMESTAMPTZ
deadline_at TIMESTAMPTZ
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
metadata JSONB DEFAULT '{}'
UNIQUE(interview_id, interviewer_id)

### TABLE: interview_questions
Questions used in an interview instance.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
interview_id UUID NOT NULL REFERENCES interviews(id)
question_text TEXT NOT NULL
question_type VARCHAR(50)
(text, video, audio, code, multiple_choice, rating_scale)
expected_duration_seconds INTEGER
candidate_answer TEXT
candidate_video_url TEXT
candidate_audio_url TEXT
candidate_code TEXT
ai_score DECIMAL(5,2)
ai_feedback TEXT
human_score DECIMAL(5,2)
human_feedback TEXT
order_index INTEGER
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
metadata JSONB DEFAULT '{}'

---

## GROUP 8: TALENT PASSPORT

### TABLE: talent_passports
The global candidate identity document.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id UUID NOT NULL REFERENCES users(id)
candidate_id UUID REFERENCES candidates(id)
passport_number VARCHAR(50) UNIQUE NOT NULL
share_link_token VARCHAR(100) UNIQUE NOT NULL
is_active BOOLEAN DEFAULT TRUE
visibility_settings JSONB DEFAULT '{}'
professional_details JSONB DEFAULT '{}'
skills JSONB DEFAULT '[]'
certifications JSONB DEFAULT '[]'
work_history JSONB DEFAULT '[]'
education JSONB DEFAULT '[]'
interview_scores JSONB DEFAULT '[]'
assessment_results JSONB DEFAULT '[]'
heat_score DECIMAL(5,2) DEFAULT 0
completeness_score DECIMAL(5,2) DEFAULT 0
view_count INTEGER DEFAULT 0
last_viewed_at TIMESTAMPTZ
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: passport_access_logs
Every access to a passport — the data control dashboard.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
passport_id UUID NOT NULL REFERENCES talent_passports(id)
accessed_by_user_id UUID REFERENCES users(id)
accessed_by_tenant_id UUID REFERENCES tenants(id)
access_type VARCHAR(50) (view, import, share, export)
ip_address VARCHAR(45)
user_agent TEXT
fields_accessed JSONB DEFAULT '[]'
imported_to_system BOOLEAN DEFAULT FALSE
revoked_at TIMESTAMPTZ
revoked_by UUID REFERENCES users(id)
accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
metadata JSONB DEFAULT '{}'

### TABLE: passport_revocations
Candidate revokes access from specific viewer.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
passport_id UUID NOT NULL REFERENCES talent_passports(id)
revoked_from_tenant_id UUID REFERENCES tenants(id)
revoked_from_user_id UUID REFERENCES users(id)
reason TEXT
revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
revoked_by UUID NOT NULL REFERENCES users(id)
metadata JSONB DEFAULT '{}'

---

## GROUP 9: INTERVIEW CAFE

### TABLE: cafe_sessions
Virtual job fair sessions.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
title VARCHAR(255) NOT NULL
description TEXT
scheduled_start TIMESTAMPTZ NOT NULL
scheduled_end TIMESTAMPTZ NOT NULL
actual_start TIMESTAMPTZ
actual_end TIMESTAMPTZ
status VARCHAR(50) DEFAULT 'scheduled'
(draft, scheduled, live, completed, cancelled)
max_candidates INTEGER DEFAULT 500
registered_count INTEGER DEFAULT 0
attended_count INTEGER DEFAULT 0
hired_count INTEGER DEFAULT 0
industries JSONB DEFAULT '[]'
roles JSONB DEFAULT '[]'
is_public BOOLEAN DEFAULT TRUE
registration_deadline TIMESTAMPTZ
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: cafe_company_booths
Company presence in a cafe session.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
session_id UUID NOT NULL REFERENCES cafe_sessions(id)
tenant_id UUID NOT NULL REFERENCES tenants(id)
booth_name VARCHAR(255)
description TEXT
available_positions JSONB DEFAULT '[]'
hr_users JSONB DEFAULT '[]'
interviewer_users JSONB DEFAULT '[]'
max_interviews INTEGER DEFAULT 50
interviews_done INTEGER DEFAULT 0
offers_made INTEGER DEFAULT 0
status VARCHAR(50) DEFAULT 'active' (active, paused, closed)
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
metadata JSONB DEFAULT '{}'
UNIQUE(session_id, tenant_id)

### TABLE: cafe_candidate_registrations
Candidate registered for a cafe session.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
session_id UUID NOT NULL REFERENCES cafe_sessions(id)
candidate_id UUID NOT NULL REFERENCES candidates(id)
passport_id UUID REFERENCES talent_passports(id)
registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
checked_in_at TIMESTAMPTZ
status VARCHAR(50) DEFAULT 'registered'
(registered, checked_in, in_queue, interviewing, completed, left)
interested_roles JSONB DEFAULT '[]'
metadata JSONB DEFAULT '{}'
UNIQUE(session_id, candidate_id)

### TABLE: cafe_interview_queue
Real-time interview queue — the POS system.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
session_id UUID NOT NULL REFERENCES cafe_sessions(id)
booth_id UUID NOT NULL REFERENCES cafe_company_booths(id)
candidate_id UUID NOT NULL REFERENCES candidates(id)
application_id UUID REFERENCES applications(id)
interview_id UUID REFERENCES interviews(id)
queue_position INTEGER
status VARCHAR(50) DEFAULT 'waiting'
(waiting, called, interviewing, completed, skipped, no_show)
called_at TIMESTAMPTZ
started_at TIMESTAMPTZ
completed_at TIMESTAMPTZ
screened_by UUID REFERENCES users(id)
screening_result VARCHAR(50) (shortlisted, rejected, hold)
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
metadata JSONB DEFAULT '{}'

---

## GROUP 10: COMMUNICATION

### TABLE: messages
All platform messages between users.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
thread_id UUID NOT NULL
sender_id UUID NOT NULL REFERENCES users(id)
recipient_id UUID REFERENCES users(id)
recipient_tenant_id UUID REFERENCES tenants(id)
message_type VARCHAR(50) DEFAULT 'text'
(text, file, template, system, whatsapp, email, sms)
content TEXT
attachments JSONB DEFAULT '[]'
is_read BOOLEAN DEFAULT FALSE
read_at TIMESTAMPTZ
related_entity_type VARCHAR(50)
related_entity_id UUID
sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: notifications
In-app notifications for all users.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
user_id UUID NOT NULL REFERENCES users(id)
title VARCHAR(255) NOT NULL
body TEXT
notification_type VARCHAR(100) NOT NULL
action_url TEXT
is_read BOOLEAN DEFAULT FALSE
read_at TIMESTAMPTZ
related_entity_type VARCHAR(50)
related_entity_id UUID
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
expires_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: email_templates
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
name VARCHAR(255) NOT NULL
subject VARCHAR(500) NOT NULL
body_html TEXT NOT NULL
body_text TEXT
template_type VARCHAR(100)
variables JSONB DEFAULT '[]'
is_active BOOLEAN DEFAULT TRUE
is_system BOOLEAN DEFAULT FALSE
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

---

## GROUP 11: DOCUMENTS

### TABLE: documents
All files and documents in the platform.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
name VARCHAR(255) NOT NULL
document_type VARCHAR(100) NOT NULL
(cv, offer_letter, contract, certificate, id_proof, assessment, other)
file_url TEXT NOT NULL
file_size INTEGER
mime_type VARCHAR(100)
related_entity_type VARCHAR(50)
related_entity_id UUID
uploaded_by UUID REFERENCES users(id)
is_verified BOOLEAN DEFAULT FALSE
verified_by UUID REFERENCES users(id)
verified_at TIMESTAMPTZ
expires_at TIMESTAMPTZ
is_confidential BOOLEAN DEFAULT FALSE
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

### TABLE: offer_letters
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
tenant_id UUID NOT NULL REFERENCES tenants(id)
application_id UUID NOT NULL REFERENCES applications(id)
candidate_id UUID NOT NULL REFERENCES candidates(id)
template_id UUID
title VARCHAR(255) NOT NULL
joining_date DATE
offered_salary DECIMAL(15,2)
salary_currency VARCHAR(10) DEFAULT 'INR'
compensation_details JSONB DEFAULT '{}'
document_id UUID REFERENCES documents(id)
status VARCHAR(50) DEFAULT 'draft'
(draft, pending_approval, sent, viewed, accepted, rejected, expired, revoked)
sent_at TIMESTAMPTZ
viewed_at TIMESTAMPTZ
accepted_at TIMESTAMPTZ
rejected_at TIMESTAMPTZ
expires_at TIMESTAMPTZ
rejection_reason TEXT
approval_chain JSONB DEFAULT '[]'
current_approver_id UUID REFERENCES users(id)
digital_signature TEXT
signed_at TIMESTAMPTZ
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by UUID REFERENCES users(id)
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
metadata JSONB DEFAULT '{}'

---

## GROUP 12: ANALYTICS (ClickHouse Tables)
These tables live in ClickHouse not PostgreSQL.
Schema uses ClickHouse data types.

### TABLE: events (ClickHouse)
Every user action tracked as event.
event_id UUID
tenant_id UUID
user_id UUID
event_type String
entity_type String
entity_id UUID
properties JSON
ip_address String
user_agent String
session_id String
created_at DateTime

### TABLE: recruitment_metrics (ClickHouse)
Pre-aggregated recruitment analytics.
tenant_id UUID
date Date
metric_type String
entity_type String
entity_id UUID
value Float64
created_at DateTime

---

## GROUP 13: AGENT MEMORY (PostgreSQL — agent_memory_db)

### TABLE: ai_memory (already exists on DB PC)
Vector storage for agent knowledge base.
id SERIAL PRIMARY KEY
content TEXT
embedding vector(384)
source VARCHAR(255)
metadata JSONB
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### TABLE: agent_tasks
Track what each agent has been assigned.
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
agent_type VARCHAR(100) NOT NULL
task_description TEXT NOT NULL
status VARCHAR(50) DEFAULT 'pending'
(pending, in_progress, completed, failed, reviewed)
input_data JSONB DEFAULT '{}'
output_data JSONB DEFAULT '{}'
error_message TEXT
started_at TIMESTAMPTZ
completed_at TIMESTAMPTZ
reviewed_by VARCHAR(100)
review_notes TEXT
langfuse_trace_id VARCHAR(255)
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

---

## INDEXES — CRITICAL FOR PERFORMANCE

Every table needs these indexes minimum:
```sql
CREATE INDEX idx_{table}_tenant ON {table}(tenant_id);
CREATE INDEX idx_{table}_tenant_deleted ON {table}(tenant_id, is_deleted);
CREATE INDEX idx_{table}_created ON {table}(created_at DESC);
```

Additional critical indexes:
```sql
-- Applications
CREATE INDEX idx_applications_candidate ON applications(tenant_id, candidate_id);
CREATE INDEX idx_applications_requisition ON applications(tenant_id, requisition_id);
CREATE INDEX idx_applications_status ON applications(tenant_id, status, is_deleted);

-- Candidates
CREATE INDEX idx_candidates_email ON candidates(tenant_id, email);
CREATE INDEX idx_candidates_hash ON candidates(global_hash);
CREATE INDEX idx_candidates_source ON candidates(tenant_id, source);

-- Action deadlines
CREATE INDEX idx_deadlines_status ON action_deadlines(tenant_id, status, deadline_at);
CREATE INDEX idx_deadlines_assigned ON action_deadlines(assigned_to, status);

-- Passport
CREATE INDEX idx_passport_token ON talent_passports(share_link_token);
CREATE INDEX idx_passport_user ON talent_passports(user_id);

-- Cafe queue
CREATE INDEX idx_cafe_queue_session ON cafe_interview_queue(session_id, status);
CREATE INDEX idx_cafe_queue_booth ON cafe_interview_queue(booth_id, status);

-- Notifications
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);

-- Audit logs
CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_record ON audit_logs(table_name, record_id);
```

---

## ROW LEVEL SECURITY POLICIES

Apply to all tables with tenant_id:
```sql
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON {table}
  USING (tenant_id = current_setting('app.tenant_id')::UUID);
```

---

## SUMMARY: TABLE COUNT BY MODULE

| Module | Tables |
|--------|--------|
| Platform and Tenants | tenants, users, user_sessions, audit_logs, platform_settings, tenant_settings |
| Organisation | departments, locations, teams |
| Jobs | job_requisitions, job_postings, job_stages |
| Candidates | candidates, candidate_profiles, candidate_notes, candidate_tags |
| Applications | applications, application_stage_history, action_deadlines |
| Agency Management | agency_client_relationships, agency_job_assignments, agency_performance_scores |
| Interviews | interview_templates, interviews, interview_panelists, interview_questions |
| Talent Passport | talent_passports, passport_access_logs, passport_revocations |
| Interview Cafe | cafe_sessions, cafe_company_booths, cafe_candidate_registrations, cafe_interview_queue |
| Communication | messages, notifications, email_templates |
| Documents | documents, offer_letters |
| Analytics (ClickHouse) | events, recruitment_metrics |
| Agent Memory | ai_memory, agent_tasks |

Total: 37 tables across all modules.
Billing and subscription tables: Not included, will be added later via admin configuration.
All feature limits managed via tenant_settings table until billing module is built.
ENDOFFILE
