"""
Central permission registry.

Every permission in the platform is defined here as a plain dict with keys:
  code        — unique identifier  "module.resource.action"
  module      — top-level domain   "candidates"
  resource    — entity type        "candidate"
  action      — verb               "view" | "create" | "edit" | "delete" | ...
  description — human readable

Adding permissions for a new module:
  1. Add entries to PERMISSION_REGISTRY below.
  2. Run:  python manage.py seed_rbac
  3. Assign the new permissions to roles in ROLE_PERMISSION_MAP below.

Future scope extension:
  When action-scoping is needed (own / team / all), add a `scope` key here
  and update RolePermission.scope accordingly.  The format will become:
    candidates.candidate.view.team
"""

# ─── Permission catalogue ─────────────────────────────────────────────────────

PERMISSION_REGISTRY = [

    # ── Jobs ─────────────────────────────────────────────────────────────────
    {'code': 'jobs.job.view',    'module': 'jobs', 'resource': 'job',    'action': 'view',    'description': 'View job requisitions and postings'},
    {'code': 'jobs.job.create',  'module': 'jobs', 'resource': 'job',    'action': 'create',  'description': 'Create job requisitions'},
    {'code': 'jobs.job.edit',    'module': 'jobs', 'resource': 'job',    'action': 'edit',    'description': 'Edit job requisitions'},
    {'code': 'jobs.job.delete',  'module': 'jobs', 'resource': 'job',    'action': 'delete',  'description': 'Delete job requisitions'},
    {'code': 'jobs.job.approve', 'module': 'jobs', 'resource': 'job',    'action': 'approve', 'description': 'Approve and publish job requisitions'},

    # ── Candidates ───────────────────────────────────────────────────────────
    {'code': 'candidates.candidate.view',   'module': 'candidates', 'resource': 'candidate', 'action': 'view',   'description': 'View candidate records'},
    {'code': 'candidates.candidate.create', 'module': 'candidates', 'resource': 'candidate', 'action': 'create', 'description': 'Add new candidates to the database'},
    {'code': 'candidates.candidate.edit',   'module': 'candidates', 'resource': 'candidate', 'action': 'edit',   'description': 'Edit candidate records'},
    {'code': 'candidates.candidate.delete', 'module': 'candidates', 'resource': 'candidate', 'action': 'delete', 'description': 'Delete candidates from the database'},
    {'code': 'candidates.note.create',      'module': 'candidates', 'resource': 'note',      'action': 'create', 'description': 'Add notes to candidate records'},
    {'code': 'candidates.note.view',        'module': 'candidates', 'resource': 'note',      'action': 'view',   'description': 'View notes on candidate records'},

    # ── Pipeline / Applications ───────────────────────────────────────────────
    {'code': 'pipeline.application.view',       'module': 'pipeline', 'resource': 'application', 'action': 'view',       'description': 'View applications and pipeline board'},
    {'code': 'pipeline.application.move_stage', 'module': 'pipeline', 'resource': 'application', 'action': 'move_stage', 'description': 'Move applications between pipeline stages'},
    {'code': 'pipeline.application.reject',     'module': 'pipeline', 'resource': 'application', 'action': 'reject',     'description': 'Reject applications'},

    # ── Interviews ────────────────────────────────────────────────────────────
    {'code': 'interviews.type.view',           'module': 'interviews', 'resource': 'type',      'action': 'view',     'description': 'View interview type registry'},
    {'code': 'interviews.type.manage',         'module': 'interviews', 'resource': 'type',      'action': 'manage',   'description': 'Create, configure and enable/disable interview types'},
    {'code': 'interviews.interview.view',      'module': 'interviews', 'resource': 'interview', 'action': 'view',     'description': 'View scheduled interviews'},
    {'code': 'interviews.interview.schedule',  'module': 'interviews', 'resource': 'interview', 'action': 'schedule', 'description': 'Schedule and update interviews'},
    {'code': 'interviews.interview.cancel',    'module': 'interviews', 'resource': 'interview', 'action': 'cancel',   'description': 'Cancel interviews'},
    {'code': 'interviews.feedback.view',       'module': 'interviews', 'resource': 'feedback',  'action': 'view',     'description': 'View interview feedback and scores'},
    {'code': 'interviews.feedback.submit',     'module': 'interviews', 'resource': 'feedback',  'action': 'submit',   'description': 'Submit interview feedback'},

    # ── Agencies ──────────────────────────────────────────────────────────────
    {'code': 'agencies.relationship.view',   'module': 'agencies', 'resource': 'relationship', 'action': 'view',   'description': 'View agency partner relationships'},
    {'code': 'agencies.relationship.manage', 'module': 'agencies', 'resource': 'relationship', 'action': 'manage', 'description': 'Invite, suspend and configure agency relationships'},
    {'code': 'agencies.assignment.view',     'module': 'agencies', 'resource': 'assignment',   'action': 'view',   'description': 'View job assignments given to agencies'},
    {'code': 'agencies.assignment.create',   'module': 'agencies', 'resource': 'assignment',   'action': 'create', 'description': 'Assign jobs to agency partners'},

    # ── Organisations ─────────────────────────────────────────────────────────
    {'code': 'organisations.settings.view', 'module': 'organisations', 'resource': 'settings', 'action': 'view', 'description': 'View organisation profile and settings'},
    {'code': 'organisations.settings.edit', 'module': 'organisations', 'resource': 'settings', 'action': 'edit', 'description': 'Update organisation profile and settings'},
    {'code': 'organisations.users.view',    'module': 'organisations', 'resource': 'users',    'action': 'view', 'description': 'View team members and their roles'},
    {'code': 'organisations.users.invite',  'module': 'organisations', 'resource': 'users',    'action': 'invite', 'description': 'Invite new users to the workspace'},
    {'code': 'organisations.users.manage',  'module': 'organisations', 'resource': 'users',    'action': 'manage', 'description': 'Change user roles, activate and deactivate users'},

    # ── Analytics ─────────────────────────────────────────────────────────────
    {'code': 'analytics.dashboard.view', 'module': 'analytics', 'resource': 'dashboard', 'action': 'view', 'description': 'View analytics and reporting dashboards'},

    # ── Communications ────────────────────────────────────────────────────────
    {'code': 'communications.email.view', 'module': 'communications', 'resource': 'email', 'action': 'view', 'description': 'View email communication history'},
    {'code': 'communications.email.send', 'module': 'communications', 'resource': 'email', 'action': 'send', 'description': 'Send emails to candidates and contacts'},
    {'code': 'communication.email_accounts.view', 'module': 'communications', 'resource': 'email_accounts', 'action': 'view', 'description': 'View connected email accounts'},
    {'code': 'communication.email_accounts.manage', 'module': 'communications', 'resource': 'email_accounts', 'action': 'manage', 'description': 'Connect, reconnect, disconnect and configure email accounts'},
    {'code': 'communication.email_templates.view', 'module': 'communications', 'resource': 'email_templates', 'action': 'view', 'description': 'View email template library'},
    {'code': 'communication.email_templates.manage', 'module': 'communications', 'resource': 'email_templates', 'action': 'manage', 'description': 'Manage tenant email templates'},
    {'code': 'communication.quick_replies.manage', 'module': 'communications', 'resource': 'quick_replies', 'action': 'manage', 'description': 'Manage quick reply templates'},
    {'code': 'communication.email.send', 'module': 'communications', 'resource': 'email', 'action': 'send', 'description': 'Send emails through communication engine'},
    {'code': 'communication.email.send_from_shared_account', 'module': 'communications', 'resource': 'email', 'action': 'send_from_shared_account', 'description': 'Send from shared tenant accounts'},
    {'code': 'communication.email.audit.view', 'module': 'communications', 'resource': 'email_audit', 'action': 'view', 'description': 'View email usage and delivery audit trail'},

    # ── Notification Control Center ───────────────────────────────────────────
    {'code': 'communication.notification_rules.view',   'module': 'communications', 'resource': 'notification_rules', 'action': 'view',   'description': 'View notification rules and channel settings'},
    {'code': 'communication.notification_rules.manage', 'module': 'communications', 'resource': 'notification_rules', 'action': 'manage', 'description': 'Create, update and delete notification rules and channel settings'},

    # ── Agency Candidate CRM ──────────────────────────────────────────────────
    {'code': 'agency_candidates.candidate.view',     'module': 'agency_candidates', 'resource': 'candidate', 'action': 'view',     'description': 'View agency talent pool and candidate profiles'},
    {'code': 'agency_candidates.candidate.create',   'module': 'agency_candidates', 'resource': 'candidate', 'action': 'create',   'description': 'Add new candidates to agency CRM'},
    {'code': 'agency_candidates.candidate.edit',     'module': 'agency_candidates', 'resource': 'candidate', 'action': 'edit',     'description': 'Edit agency candidate records'},
    {'code': 'agency_candidates.candidate.delete',   'module': 'agency_candidates', 'resource': 'candidate', 'action': 'delete',   'description': 'Delete candidates from agency CRM'},
    {'code': 'agency_candidates.candidate.assign',   'module': 'agency_candidates', 'resource': 'candidate', 'action': 'assign',   'description': 'Assign candidates to recruiters'},
    {'code': 'agency_candidates.candidate.transfer', 'module': 'agency_candidates', 'resource': 'candidate', 'action': 'transfer', 'description': 'Transfer candidate ownership between recruiters'},
    {'code': 'agency_candidates.candidate.submit',   'module': 'agency_candidates', 'resource': 'candidate', 'action': 'submit',   'description': 'Submit candidates to client jobs'},
    {'code': 'agency_candidates.hotlist.manage',     'module': 'agency_candidates', 'resource': 'hotlist',   'action': 'manage',   'description': 'Create and manage candidate hotlists'},
]

# Convenience: set of all codes for role assignment helpers below
_ALL_CODES = {p['code'] for p in PERMISSION_REGISTRY}


# ─── Role definitions ─────────────────────────────────────────────────────────

ROLE_DEFINITIONS = [
    {'name': 'super_admin',       'display_name': 'Super Admin',        'description': 'Platform-level administrator with unrestricted access'},
    {'name': 'tenant_admin',      'display_name': 'Tenant Admin',       'description': 'Workspace administrator with full access within their tenant'},
    {'name': 'hr_manager',        'display_name': 'HR Manager',         'description': 'Senior HR role with broad access to hiring and people operations'},
    {'name': 'hiring_manager',    'display_name': 'Hiring Manager',     'description': 'Business-side manager who owns job requirements and interviews'},
    {'name': 'recruiter',         'display_name': 'Recruiter',          'description': 'Sourcing and pipeline management for open requisitions'},
    {'name': 'interviewer',       'display_name': 'Interviewer',        'description': 'Participates in interview panels and submits feedback'},
    {'name': 'viewer',            'display_name': 'Viewer',             'description': 'Read-only access to seeded modules'},
    {'name': 'agency_owner',      'display_name': 'Agency Owner',       'description': 'Owner/admin of a recruitment agency tenant'},
    {'name': 'agency_admin',      'display_name': 'Agency Admin',       'description': 'Senior agency staff with management access'},
    {'name': 'agency_manager',    'display_name': 'Agency Manager',      'description': 'Agency team leader or manager'},
    {'name': 'agency_recruiter',  'display_name': 'Agency Recruiter',   'description': 'Agency-side recruiter working assigned jobs'},
    {'name': 'agency_sourcer',    'display_name': 'Agency Sourcer',     'description': 'Agency staff focused on sourcing candidates for the pool'},
    {'name': 'candidate',         'display_name': 'Candidate',          'description': 'Self-registered candidate with access to the candidate portal only'},
]

# ─── Role → permission mapping ────────────────────────────────────────────────
# Use the constant '__all__' to grant every registered permission.
# Otherwise list explicit permission codes.

ROLE_PERMISSION_MAP = {

    'super_admin': '__all__',
    'tenant_admin': '__all__',

    'hr_manager': [
        # Jobs — full
        'jobs.job.view', 'jobs.job.create', 'jobs.job.edit', 'jobs.job.delete', 'jobs.job.approve',
        # Candidates — full
        'candidates.candidate.view', 'candidates.candidate.create', 'candidates.candidate.edit', 'candidates.candidate.delete',
        'candidates.note.view', 'candidates.note.create',
        # Pipeline — full
        'pipeline.application.view', 'pipeline.application.move_stage', 'pipeline.application.reject',
        # Interviews — full
        'interviews.type.view', 'interviews.type.manage',
        'interviews.interview.view', 'interviews.interview.schedule', 'interviews.interview.cancel',
        'interviews.feedback.view', 'interviews.feedback.submit',
        # Agencies — view + manage
        'agencies.relationship.view', 'agencies.relationship.manage',
        'agencies.assignment.view', 'agencies.assignment.create',
        # Org — view settings, manage users
        'organisations.settings.view',
        'organisations.users.view', 'organisations.users.invite', 'organisations.users.manage',
        # Analytics, comms
        'analytics.dashboard.view',
        'communications.email.view', 'communications.email.send',
        'communication.email_accounts.view', 'communication.email_accounts.manage',
        'communication.email_templates.view', 'communication.email_templates.manage',
        'communication.quick_replies.manage',
        'communication.email.send', 'communication.email.send_from_shared_account',
        'communication.email.audit.view',
    ],

    'recruiter': [
        'jobs.job.view', 'jobs.job.create', 'jobs.job.edit',
        'candidates.candidate.view', 'candidates.candidate.create', 'candidates.candidate.edit',
        'candidates.note.view', 'candidates.note.create',
        'pipeline.application.view', 'pipeline.application.move_stage',
        'interviews.type.view',
        'interviews.interview.view', 'interviews.interview.schedule',
        'interviews.feedback.view',
        'agencies.relationship.view', 'agencies.assignment.view',
        'organisations.settings.view', 'organisations.users.view',
        'analytics.dashboard.view',
        'communications.email.view', 'communications.email.send',
        'communication.email_accounts.view', 'communication.email_accounts.manage',
        'communication.email_templates.view', 'communication.email_templates.manage',
        'communication.quick_replies.manage',
        'communication.email.send', 'communication.email.send_from_shared_account',
        'communication.email.audit.view',
    ],

    'hiring_manager': [
        'jobs.job.view', 'jobs.job.create', 'jobs.job.approve',
        'candidates.candidate.view', 'candidates.note.view', 'candidates.note.create',
        'pipeline.application.view', 'pipeline.application.reject',
        'interviews.type.view',
        'interviews.interview.view', 'interviews.interview.schedule',
        'interviews.feedback.view', 'interviews.feedback.submit',
        'organisations.settings.view', 'organisations.users.view',
        'analytics.dashboard.view',
        # Communications — view-only: can see email history and account status, cannot manage accounts
        'communications.email.view',
        'communication.email_accounts.view',
        'communication.email_templates.view',
    ],

    'interviewer': [
        'candidates.candidate.view', 'candidates.note.view',
        'interviews.type.view',
        'interviews.interview.view',
        'interviews.feedback.view', 'interviews.feedback.submit',
    ],

    'viewer': [
        # Read-only access to all seeded view permissions
        'jobs.job.view',
        'candidates.candidate.view', 'candidates.note.view',
        'pipeline.application.view',
        'interviews.type.view',
        'interviews.interview.view', 'interviews.feedback.view',
        'agencies.relationship.view', 'agencies.assignment.view',
        'organisations.settings.view', 'organisations.users.view',
        'analytics.dashboard.view',
        'communications.email.view',
        'communication.email_accounts.view',
        'communication.email_templates.view',
        'communication.email.audit.view',
    ],

    # Agency roles — scoped to their own agency operations
    'agency_owner': [
        'jobs.job.view',
        'candidates.candidate.view', 'candidates.candidate.create', 'candidates.candidate.edit',
        'candidates.note.view', 'candidates.note.create',
        'pipeline.application.view', 'pipeline.application.move_stage',
        'interviews.type.view',
        'interviews.interview.view',
        'agencies.relationship.view', 'agencies.relationship.manage',
        'agencies.assignment.view', 'agencies.assignment.create',
        'organisations.settings.view', 'organisations.settings.edit',
        'organisations.users.view', 'organisations.users.invite', 'organisations.users.manage',
        'analytics.dashboard.view',
        'communications.email.view', 'communications.email.send',
        'communication.email_accounts.view', 'communication.email_accounts.manage',
        'communication.email_templates.view', 'communication.email_templates.manage',
        'communication.quick_replies.manage',
        'communication.email.send', 'communication.email.send_from_shared_account',
        'communication.email.audit.view',
        # Agency CRM
        'agency_candidates.candidate.view', 'agency_candidates.candidate.create',
        'agency_candidates.candidate.edit', 'agency_candidates.candidate.delete',
        'agency_candidates.candidate.assign', 'agency_candidates.candidate.transfer',
        'agency_candidates.candidate.submit', 'agency_candidates.hotlist.manage',
    ],

    'agency_admin': [
        'jobs.job.view',
        'candidates.candidate.view', 'candidates.candidate.create', 'candidates.candidate.edit',
        'candidates.note.view', 'candidates.note.create',
        'pipeline.application.view', 'pipeline.application.move_stage',
        'interviews.type.view',
        'interviews.interview.view',
        'agencies.relationship.view',
        'agencies.assignment.view', 'agencies.assignment.create',
        'organisations.settings.view',
        'organisations.users.view', 'organisations.users.invite',
        'analytics.dashboard.view',
        'communications.email.view', 'communications.email.send',
        'communication.email_accounts.view', 'communication.email_accounts.manage',
        'communication.email_templates.view', 'communication.email_templates.manage',
        'communication.quick_replies.manage',
        'communication.email.send', 'communication.email.send_from_shared_account',
        'communication.email.audit.view',
        # Agency CRM
        'agency_candidates.candidate.view', 'agency_candidates.candidate.create',
        'agency_candidates.candidate.edit', 'agency_candidates.candidate.delete',
        'agency_candidates.candidate.assign', 'agency_candidates.candidate.transfer',
        'agency_candidates.candidate.submit', 'agency_candidates.hotlist.manage',
    ],

    'agency_manager': [
        'jobs.job.view',
        'candidates.candidate.view', 'candidates.note.view',
        'pipeline.application.view', 'pipeline.application.move_stage',
        'interviews.interview.view',
        'agencies.assignment.view',
        'organisations.users.view',
        'analytics.dashboard.view',
        'communications.email.view', 'communications.email.send',
        'communication.email_templates.view',
        # Agency CRM
        'agency_candidates.candidate.view', 'agency_candidates.candidate.create',
        'agency_candidates.candidate.edit', 'agency_candidates.candidate.assign',
        'agency_candidates.candidate.transfer', 'agency_candidates.candidate.submit',
        'agency_candidates.hotlist.manage',
    ],

    'agency_recruiter': [
        'jobs.job.view',
        'candidates.candidate.view', 'candidates.candidate.create', 'candidates.candidate.edit',
        'candidates.note.view', 'candidates.note.create',
        'pipeline.application.view', 'pipeline.application.move_stage',
        'interviews.type.view',
        'interviews.interview.view',
        'agencies.assignment.view',
        'communications.email.view', 'communications.email.send',
        'communication.email_accounts.view',
        'communication.email_templates.view',
        'communication.email.send',
        # Agency CRM
        'agency_candidates.candidate.view', 'agency_candidates.candidate.create',
        'agency_candidates.candidate.edit', 'agency_candidates.candidate.submit',
        'agency_candidates.hotlist.manage',
    ],

    'agency_sourcer': [
        'jobs.job.view',
        'candidates.candidate.view', 'candidates.candidate.create', 'candidates.candidate.edit',
        'agency_candidates.candidate.view', 'agency_candidates.candidate.create',
        'agency_candidates.candidate.edit', 'agency_candidates.hotlist.manage',
    ],


def resolve_permission_codes(role_name: str) -> set:
    """Return the set of permission codes for a role, expanding '__all__'."""
    mapping = ROLE_PERMISSION_MAP.get(role_name, [])
    if mapping == '__all__':
        return set(_ALL_CODES)
    return set(mapping)
