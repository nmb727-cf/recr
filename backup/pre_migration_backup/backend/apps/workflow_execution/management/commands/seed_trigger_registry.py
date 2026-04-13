"""
Management command: seed_trigger_registry
==========================================
Seeds the WorkflowEventDefinition registry with all standard system trigger events
required by the workflow execution engine.

Usage:
    python manage.py seed_trigger_registry
    python manage.py seed_trigger_registry --reset   # deactivate unlisted events first
"""
from django.core.management.base import BaseCommand
from apps.orchestration_center.models.event_trigger import WorkflowEventDefinition

TRIGGER_EVENTS = [
    # Jobs
    {'event_key': 'job_created',  'event_name': 'Job Created',  'module_scope': 'jobs', 'entity_type': 'job',
     'payload_schema': {'job_id': 'str', 'title': 'str', 'department': 'str', 'status': 'str'}},
    {'event_key': 'job_updated',  'event_name': 'Job Updated',  'module_scope': 'jobs', 'entity_type': 'job',
     'payload_schema': {'job_id': 'str'}},
    {'event_key': 'job_approved', 'event_name': 'Job Approved', 'module_scope': 'jobs', 'entity_type': 'job',
     'payload_schema': {'job_id': 'str', 'status': 'str'}},
    {'event_key': 'job_published','event_name': 'Job Published','module_scope': 'jobs', 'entity_type': 'job',
     'payload_schema': {'job_id': 'str', 'status': 'str'}},

    # Candidates
    {'event_key': 'candidate_created',        'event_name': 'Candidate Created',        'module_scope': 'candidates', 'entity_type': 'candidate'},
    {'event_key': 'candidate_updated',        'event_name': 'Candidate Updated',        'module_scope': 'candidates', 'entity_type': 'candidate'},
    {'event_key': 'candidate_applied',        'event_name': 'Candidate Applied',        'module_scope': 'pipeline',   'entity_type': 'application',
     'payload_schema': {'application_id': 'str', 'candidate_id': 'str', 'job_id': 'str', 'source': 'str'}},
    {'event_key': 'candidate_added',          'event_name': 'Candidate Added',          'module_scope': 'pipeline',   'entity_type': 'application',
     'payload_schema': {'application_id': 'str', 'candidate_id': 'str', 'job_id': 'str', 'source': 'str'}},
    {'event_key': 'candidate_status_changed', 'event_name': 'Candidate Status Changed', 'module_scope': 'candidates', 'entity_type': 'candidate'},

    # Agency
    {'event_key': 'agency_submission_created',    'event_name': 'Agency Submission Created',    'module_scope': 'agencies', 'entity_type': 'agency_submission',
     'payload_schema': {'submission_id': 'str', 'agency_id': 'str', 'candidate_id': 'str', 'job_id': 'str'}},
    {'event_key': 'agency_submission_reviewed',   'event_name': 'Agency Submission Reviewed',   'module_scope': 'agencies', 'entity_type': 'agency_submission'},
    {'event_key': 'agency_submission_shortlisted','event_name': 'Agency Submission Shortlisted','module_scope': 'agencies', 'entity_type': 'agency_submission'},
    {'event_key': 'agency_submission_rejected',   'event_name': 'Agency Submission Rejected',   'module_scope': 'agencies', 'entity_type': 'agency_submission'},

    # Pipeline
    {'event_key': 'stage_entered',        'event_name': 'Stage Entered',        'module_scope': 'pipeline', 'entity_type': 'application'},
    {'event_key': 'stage_changed',        'event_name': 'Stage Changed',        'module_scope': 'pipeline', 'entity_type': 'application'},
    {'event_key': 'candidate_shortlisted','event_name': 'Candidate Shortlisted','module_scope': 'pipeline', 'entity_type': 'application'},
    {'event_key': 'candidate_rejected',   'event_name': 'Candidate Rejected',   'module_scope': 'pipeline', 'entity_type': 'application'},

    # Interview
    {'event_key': 'interview_created',           'event_name': 'Interview Created',            'module_scope': 'interviews', 'entity_type': 'interview'},
    {'event_key': 'interview_scheduled',         'event_name': 'Interview Scheduled',          'module_scope': 'interviews', 'entity_type': 'interview'},
    {'event_key': 'interview_completed',         'event_name': 'Interview Completed',          'module_scope': 'interviews', 'entity_type': 'interview',
     'payload_schema': {'interview_id': 'str', 'candidate_id': 'str', 'application_id': 'str', 'overall_score': 'float'}},
    {'event_key': 'interview_feedback_submitted','event_name': 'Interview Feedback Submitted', 'module_scope': 'interviews', 'entity_type': 'interview'},

    # Offer
    {'event_key': 'offer_created',  'event_name': 'Offer Created',  'module_scope': 'offers', 'entity_type': 'application'},
    {'event_key': 'offer_approved', 'event_name': 'Offer Approved', 'module_scope': 'offers', 'entity_type': 'application'},
    {'event_key': 'offer_sent',     'event_name': 'Offer Sent',     'module_scope': 'offers', 'entity_type': 'application'},
    {'event_key': 'offer_accepted', 'event_name': 'Offer Accepted', 'module_scope': 'offers', 'entity_type': 'application',
     'payload_schema': {'application_id': 'str', 'candidate_id': 'str'}},
    {'event_key': 'offer_rejected', 'event_name': 'Offer Rejected', 'module_scope': 'offers', 'entity_type': 'application'},

    # Onboarding
    {'event_key': 'onboarding_started',   'event_name': 'Onboarding Started',   'module_scope': 'onboarding', 'entity_type': 'application'},
    {'event_key': 'onboarding_completed', 'event_name': 'Onboarding Completed', 'module_scope': 'onboarding', 'entity_type': 'application'},
    {'event_key': 'hrms_handoff_ready',   'event_name': 'HRMS Handoff Ready',   'module_scope': 'onboarding', 'entity_type': 'application'},

    # Tasks
    {'event_key': 'task_created',   'event_name': 'Task Created',   'module_scope': 'tasks', 'entity_type': 'task'},
    {'event_key': 'task_completed', 'event_name': 'Task Completed', 'module_scope': 'tasks', 'entity_type': 'task'},
    {'event_key': 'task_overdue',   'event_name': 'Task Overdue',   'module_scope': 'tasks', 'entity_type': 'task'},

    # SLA
    {'event_key': 'sla_created',     'event_name': 'SLA Created',     'module_scope': 'sla', 'entity_type': 'sla'},
    {'event_key': 'sla_warning_due', 'event_name': 'SLA Warning Due', 'module_scope': 'sla', 'entity_type': 'sla'},
    {'event_key': 'sla_breached',    'event_name': 'SLA Breached',    'module_scope': 'sla', 'entity_type': 'sla'},
    {'event_key': 'sla_completed',   'event_name': 'SLA Completed',   'module_scope': 'sla', 'entity_type': 'sla'},

    # Resume / advance events (do not start workflows, only resume waiting ones)
    {'event_key': 'approval_received',          'event_name': 'Approval Received',          'module_scope': 'approvals',   'entity_type': 'approval'},
    {'event_key': 'recruiter_review_completed', 'event_name': 'Recruiter Review Completed', 'module_scope': 'pipeline',    'entity_type': 'application'},
    {'event_key': 'client_feedback_received',   'event_name': 'Client Feedback Received',   'module_scope': 'pipeline',    'entity_type': 'application'},
    {'event_key': 'candidate_response_received','event_name': 'Candidate Response Received','module_scope': 'candidates',  'entity_type': 'candidate'},
    {'event_key': 'document_signed',            'event_name': 'Document Signed',            'module_scope': 'documents',   'entity_type': 'document'},
    {'event_key': 'offer_counter_received',     'event_name': 'Offer Counter Received',     'module_scope': 'offers',      'entity_type': 'application'},
]


class Command(BaseCommand):
    help = 'Seed the workflow trigger registry with all standard system events.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Deactivate any existing registry entries not in this seed list.',
        )

    def handle(self, *args, **options):
        seeded_keys = set()
        created_count = 0
        updated_count = 0

        for entry in TRIGGER_EVENTS:
            key = entry['event_key']
            seeded_keys.add(key)
            defaults = {
                'event_name':     entry['event_name'],
                'module_scope':   entry['module_scope'],
                'description':    entry.get('description', ''),
                'payload_schema': entry.get('payload_schema', {}),
                'is_active':      True,
            }
            obj, created = WorkflowEventDefinition.objects.update_or_create(
                event_key=key,
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        if options['reset']:
            deactivated = WorkflowEventDefinition.objects.exclude(
                event_key__in=seeded_keys
            ).update(is_active=False)
            self.stdout.write(self.style.WARNING(f'Deactivated {deactivated} unlisted event(s).'))

        self.stdout.write(
            self.style.SUCCESS(
                f'Trigger registry seeded: {created_count} created, {updated_count} updated.'
            )
        )
