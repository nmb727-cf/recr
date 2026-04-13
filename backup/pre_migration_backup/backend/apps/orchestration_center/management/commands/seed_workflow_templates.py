from django.core.management.base import BaseCommand
from apps.orchestration_center.models.workflow import WorkflowTemplate

class Command(BaseCommand):
    help = 'Seed system workflow templates'

    def handle(self, *args, **options):
        templates = [
            {
                'name': 'Candidate Follow-up Sequence',
                'description': 'Wait 24 hours after application. If no candidate response, send follow-up email.',
                'category': 'Candidate Automation',
                'trigger_event': 'candidate_applied',
                'template_json': {
                    'nodes': [
                        {'id': 'start', 'type': 'start', 'config': {}},
                        {'id': 'delay_1', 'type': 'delay', 'config': {'duration': 24, 'unit': 'hours'}},
                        {'id': 'check_response', 'type': 'condition', 'config': {'field': 'has_responded', 'operator': 'equals', 'value': False}},
                        {'id': 'send_email', 'type': 'action', 'config': {'type': 'send_email', 'template': 'candidate_followup'}},
                        {'id': 'end', 'type': 'end', 'config': {}}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'delay_1'},
                        {'source': 'delay_1', 'target': 'check_response'},
                        {'source': 'check_response', 'target': 'send_email', 'condition': {'value': True}},
                        {'source': 'send_email', 'target': 'end'}
                    ]
                }
            },
            {
                'name': 'Auto-Assign Recruiter',
                'description': 'Assign a default recruiter and notify them immediately when a candidate applies.',
                'category': 'Recruiter Automation',
                'trigger_event': 'candidate_applied',
                'template_json': {
                    'nodes': [
                        {'id': 'start', 'type': 'start', 'config': {}},
                        {'id': 'assign', 'type': 'action', 'config': {'type': 'assign_user', 'role': 'recruiter'}},
                        {'id': 'notify', 'type': 'action', 'config': {'type': 'notify_user', 'message': 'New candidate assigned'}},
                        {'id': 'end', 'type': 'end', 'config': {}}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'assign'},
                        {'source': 'assign', 'target': 'notify'},
                        {'source': 'notify', 'target': 'end'}
                    ]
                }
            },
            {
                'name': 'Interview Reminder',
                'description': 'Send a reminder to candidate and panel 24 hours before the scheduled interview.',
                'category': 'Interview Automation',
                'trigger_event': 'interview_scheduled',
                'template_json': {
                    'nodes': [
                        {'id': 'start', 'type': 'start', 'config': {}},
                        {'id': 'delay', 'type': 'delay', 'config': {'duration': 24, 'unit': 'hours', 'relative_to': 'interview_at'}},
                        {'id': 'notify', 'type': 'action', 'config': {'type': 'send_email', 'template': 'interview_reminder'}},
                        {'id': 'end', 'type': 'end', 'config': {}}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'delay'},
                        {'source': 'delay', 'target': 'notify'},
                        {'source': 'notify', 'target': 'end'}
                    ]
                }
            },
            {
                'name': 'Offer Reminder',
                'description': 'Wait 48 hours after offer is sent. If not accepted, send a reminder email.',
                'category': 'Offer Automation',
                'trigger_event': 'offer_sent',
                'template_json': {
                    'nodes': [
                        {'id': 'start', 'type': 'start', 'config': {}},
                        {'id': 'delay', 'type': 'delay', 'config': {'duration': 48, 'unit': 'hours'}},
                        {'id': 'check_status', 'type': 'condition', 'config': {'field': 'offer_status', 'operator': 'equals', 'value': 'sent'}},
                        {'id': 'notify', 'type': 'action', 'config': {'type': 'send_email', 'template': 'offer_reminder'}},
                        {'id': 'end', 'type': 'end', 'config': {}}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'delay'},
                        {'source': 'delay', 'target': 'check_status'},
                        {'source': 'check_status', 'target': 'notify', 'condition': {'value': True}},
                        {'source': 'notify', 'target': 'end'}
                    ]
                }
            },
            {
                'name': 'SLA Escalation',
                'description': 'Notify manager and escalate if a job deadline is missed.',
                'category': 'SLA Automation',
                'trigger_event': 'deadline_missed',
                'template_json': {
                    'nodes': [
                        {'id': 'start', 'type': 'start', 'config': {}},
                        {'id': 'notify_mgr', 'type': 'action', 'config': {'type': 'notify_user', 'target': 'manager'}},
                        {'id': 'escalate', 'type': 'action', 'config': {'type': 'escalate_job'}},
                        {'id': 'end', 'type': 'end', 'config': {}}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'notify_mgr'},
                        {'source': 'notify_mgr', 'target': 'escalate'},
                        {'source': 'escalate', 'target': 'end'}
                    ]
                }
            },
            {
                'name': 'Agency Submission Follow-up',
                'description': 'Notify recruiter when an agency submits a new candidate.',
                'category': 'Agency Automation',
                'trigger_event': 'agency_submitted',
                'template_json': {
                    'nodes': [
                        {'id': 'start', 'type': 'start', 'config': {}},
                        {'id': 'notify', 'type': 'action', 'config': {'type': 'notify_user', 'message': 'New agency submission'}},
                        {'id': 'end', 'type': 'end', 'config': {}}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'notify'},
                        {'source': 'notify', 'target': 'end'}
                    ]
                }
            },
            {
                'name': 'Stage Movement Automation',
                'description': 'Send welcome email and assign onboarding task when candidate moves to "Joined" stage.',
                'category': 'Pipeline Automation',
                'trigger_event': 'candidate_moved_stage',
                'template_json': {
                    'nodes': [
                        {'id': 'start', 'type': 'start', 'config': {}},
                        {'id': 'check_stage', 'type': 'condition', 'config': {'field': 'new_stage', 'operator': 'equals', 'value': 'joined'}},
                        {'id': 'send_email', 'type': 'action', 'config': {'type': 'send_email', 'template': 'onboarding_welcome'}},
                        {'id': 'assign_task', 'type': 'action', 'config': {'type': 'create_task', 'title': 'Onboarding Setup'}},
                        {'id': 'end', 'type': 'end', 'config': {}}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'check_stage'},
                        {'source': 'check_stage', 'target': 'send_email', 'condition': {'value': True}},
                        {'source': 'send_email', 'target': 'assign_task'},
                        {'source': 'assign_task', 'target': 'end'}
                    ]
                }
            },
            {
                'name': 'Interview Task Creation',
                'description': 'Create a feedback task for interviewers immediately after an interview is completed.',
                'category': 'Pipeline Automation',
                'trigger_event': 'interview_completed',
                'template_json': {
                    'nodes': [
                        {'id': 'start', 'type': 'start', 'config': {}},
                        {'id': 'create_task', 'type': 'action', 'config': {'type': 'create_task', 'title': 'Submit Interview Feedback'}},
                        {'id': 'end', 'type': 'end', 'config': {}}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'create_task'},
                        {'source': 'create_task', 'target': 'end'}
                    ]
                }
            },
            {
                'name': 'Hiring Manager Notification',
                'description': 'Notify hiring manager when a candidate reaches the final interview stage.',
                'category': 'Pipeline Automation',
                'trigger_event': 'candidate_moved_stage',
                'template_json': {
                    'nodes': [
                        {'id': 'start', 'type': 'start', 'config': {}},
                        {'id': 'check_stage', 'type': 'condition', 'config': {'field': 'new_stage', 'operator': 'equals', 'value': 'final_interview'}},
                        {'id': 'notify', 'type': 'action', 'config': {'type': 'notify_user', 'target': 'hiring_manager'}},
                        {'id': 'end', 'type': 'end', 'config': {}}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'check_stage'},
                        {'source': 'check_stage', 'target': 'notify', 'condition': {'value': True}},
                        {'source': 'notify', 'target': 'end'}
                    ]
                }
            },
            {
                'name': 'Candidate Rejection Automation',
                'description': 'Wait 2 hours after a candidate is rejected, then send a polite rejection email.',
                'category': 'Candidate Automation',
                'trigger_event': 'candidate_moved_stage',
                'template_json': {
                    'nodes': [
                        {'id': 'start', 'type': 'start', 'config': {}},
                        {'id': 'check_stage', 'type': 'condition', 'config': {'field': 'new_stage', 'operator': 'equals', 'value': 'rejected'}},
                        {'id': 'delay', 'type': 'delay', 'config': {'duration': 2, 'unit': 'hours'}},
                        {'id': 'send_email', 'type': 'action', 'config': {'type': 'send_email', 'template': 'polite_rejection'}},
                        {'id': 'end', 'type': 'end', 'config': {}}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'check_stage'},
                        {'source': 'check_stage', 'target': 'delay', 'condition': {'value': True}},
                        {'source': 'delay', 'target': 'send_email'},
                        {'source': 'send_email', 'target': 'end'}
                    ]
                }
            }
        ]

        for t in templates:
            WorkflowTemplate.objects.update_or_create(
                name=t['name'],
                defaults=t
            )
            self.stdout.write(self.style.SUCCESS(f"Seeded workflow template: {t['name']}"))
