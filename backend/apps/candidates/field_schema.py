"""
Canonical Candidate Field Schema
==================================
Backend single source of truth for all candidate field option sets,
validation constants, and storage mapping notes.

Import from here in models, serializers, and views so the same values
are never defined more than once.

See also: frontend/src/constants/candidateFields.ts (keep in sync)
"""

# ── Work authorization ─────────────────────────────────────────────────────────
WORK_AUTHORIZATION_CHOICES = [
    ('citizen',              'Citizen / National'),
    ('permanent_resident',   'Permanent Resident'),
    ('work_visa',            'Work Visa / Work Permit'),
    ('sponsorship_required', 'Requires Sponsorship'),
    ('not_specified',        'Prefer not to say'),
]

# Values list — use for CharField choices= parameter.
WORK_AUTHORIZATION_VALUES = [v for v, _ in WORK_AUTHORIZATION_CHOICES]

# ── Education levels ───────────────────────────────────────────────────────────
EDUCATION_CHOICES = [
    ('high_school', 'High School / Secondary'),
    ('diploma',     'Diploma / Certificate'),
    ('bachelor',    "Bachelor's Degree"),
    ('master',      "Master's Degree"),
    ('phd',         'PhD / Doctorate'),
    ('other',       'Other'),
]

EDUCATION_VALUES = [v for v, _ in EDUCATION_CHOICES]

# ── Work mode preferences ──────────────────────────────────────────────────────
# Used as Candidate.work_mode_preference AND Passport.preferred_work_mode.
# The field name differs across models but the values and labels must match.
WORK_MODE_CHOICES = [
    ('any',    'Open to Any'),
    ('remote', 'Remote Only'),
    ('hybrid', 'Hybrid'),
    ('onsite', 'On-site Only'),
]

WORK_MODE_VALUES = [v for v, _ in WORK_MODE_CHOICES]

# ── Availability status ────────────────────────────────────────────────────────
AVAILABILITY_STATUS_CHOICES = [
    ('available_now',  'Available Now'),
    ('notice_period',  'Serving Notice Period'),
    ('open_to_offers', 'Open to Offers'),
    ('not_looking',    'Not Currently Looking'),
]

AVAILABILITY_STATUS_VALUES = [v for v, _ in AVAILABILITY_STATUS_CHOICES]

# ── Source options ─────────────────────────────────────────────────────────────
SOURCE_CHOICES = [
    ('self',      'Self Registered'),
    ('agency',    'Agency'),
    ('company',   'Company / Internal'),
    ('linkedin',  'LinkedIn'),
    ('referral',  'Referral'),
    ('job_board', 'Job Board'),
    ('passport',  'Talent Passport'),
    ('cafe',      'Interview Café'),
    ('other',     'Other'),
]

SOURCE_VALUES = [v for v, _ in SOURCE_CHOICES]

# ── Initial entry type ─────────────────────────────────────────────────────────
# How the candidate record was first created — stored immutably.
INITIAL_ENTRY_TYPE_CHOICES = [
    ('self',           'Self / Direct Signup'),          # Source 3
    ('invite',         'Invited via Claim Link'),        # Source 1
    ('manual',         'Manual Entry by Recruiter'),     # Source 1 (quick/detailed add)
    ('quick_add',      'Quick Add'),                     # Source 1
    ('detailed_add',   'Detailed Add'),                  # Source 1
    ('invite_candidate', 'Invite Candidate'),            # Source 1
    ('invite_link',    'Apply Link / Public Form'),      # Source 2
    ('upload_resume',  'Resume Upload'),
    ('import_passport', 'Passport Import'),
    ('agency_submit',  'Agency Submission'),
]

# ── Account status ─────────────────────────────────────────────────────────────
ACCOUNT_STATUS_CHOICES = [
    ('none',    'No account'),
    ('invited', 'Invite sent — awaiting signup'),
    ('claimed', 'Account created and claimed'),
    ('active',  'Active'),
]

# ── Coverage matrix ────────────────────────────────────────────────────────────
# Documents which fields each entry point captures.
# Use to audit gaps and drive QA.
#
# Key:  ✅ present  ⚠️ partial/different name  ❌ missing
#
# Field                    | quick_add | detailed_add | apply_link | onboarding | register |
# ──────────────────────────────────────────────────────────────────────────────────────────
# first_name               |    ✅     |      ✅      |     ✅     |     ✅     |    ✅    |
# last_name                |    ✅     |      ✅      |     ✅     |     ✅     |    ✅    |
# email                    |    ✅     |      ✅      |     ✅     |     —      |    ✅    |
# phone                    |    ✅     |      ✅      |     ✅     |     ✅     |    ✅    |
# linkedin_url             |    ❌     |      ✅      |     ✅     |     ❌     |    ❌    |
# current_title            |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
# current_company          |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
# current_location_city    |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
# current_location_country |    ❌     |      ✅      |     ❌     |     ✅     |    ❌    |
# experience_years         |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
# relevant_experience_years|    ❌     |      ❌      |     ✅     |     ❌     |    ❌    |
# highest_education        |    ❌     |      ❌      |     ✅     |     ❌     |    ❌    |
# graduation_year          |    ❌     |      ❌      |     ✅     |     ❌     |    ❌    |
# skills                   |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
# languages                |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
# nationality              |    ❌     |      ✅      |     ✅     |     ❌     |    ❌    |
# work_authorization       |    ❌     |    ⚠️       |    ⚠️     |     ❌     |    ❌    |
# availability_status      |    ❌     |      ❌      |     ✅     |     ❌     |    ❌    |
# notice_period_days       |    ❌     |      ✅      |     ✅     |     ✅     |    ❌    |
# last_working_day         |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
# is_actively_looking      |    ❌     |      ✅      |     ❌     |     ✅     |    ❌    |
# work_mode_preference     |    ❌     |      ❌      |     ✅     |     ✅     |    ❌    |
# expected_salary_min/max  |    ❌     |      ✅      |     ❌     |     ✅     |    ❌    |
# salary_currency          |    ❌     |      ✅      |     ❌     |     ✅     |    ❌    |
# offer_in_hand            |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
# resume_url               |    ✅     |      ✅      |     ✅     |     ✅     |    ❌    |
# source                   |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
# tags                     |    ❌     |      ✅      |     ❌     |     ❌     |    ❌    |
