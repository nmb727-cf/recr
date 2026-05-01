from django.core.management.base import BaseCommand
from apps.orchestration_center.models import AutomationLibraryTemplate

class Command(BaseCommand):
    help = 'Seed system automation templates'

    def handle(self, *args, **options):
        templates = [
            {
                'template_name': 'Candidate Follow-up Sequence',
                'template_type': 'followup_sequence',
                'description': 'Automated follow-up sequence for candidates who haven\'t responded to interview invites.',
                'category': 'candidate_followup',
                'risk_level': 'low',
                'config_payload': {
                    'suggestion_type': 'followup_recommendation',
                    'confidence_threshold': 0.8,
                    'auto_approve': True,
                    'auto_apply': False
                },
                'is_system_template': True
            },
            {
                'template_name': 'SLA Escalation Workflow',
                'template_type': 'escalation_workflow',
                'description': 'Escalate jobs that have been stuck in a stage beyond the defined SLA.',
                'category': 'compliance',
                'risk_level': 'medium',
                'config_payload': {
                    'suggestion_type': 'escalation_recommendation',
                    'confidence_threshold': 0.9,
                    'auto_approve': False,
                    'auto_apply': False
                },
                'is_system_template': True
            },
            {
                'template_name': 'Interview Panel Reminder',
                'template_type': 'reminder_workflow',
                'description': 'Send automated reminders to interviewers 24 hours before the scheduled time.',
                'category': 'interview',
                'risk_level': 'low',
                'config_payload': {
                    'suggestion_type': 'communication_draft',
                    'module_scope': 'interviews',
                    'confidence_threshold': 0.7,
                    'auto_approve': True,
                    'auto_apply': True
                },
                'is_system_template': True
            },
            {
                'template_name': 'Critical Hiring Decision Guardrail',
                'template_type': 'decision_workflow',
                'description': 'Governance workflow for high-stakes hiring decisions requiring dual-approver consensus.',
                'category': 'decision_support',
                'risk_level': 'critical',
                'config_payload': {
                    'suggestion_type': 'review_recommendation',
                    'confidence_threshold': 0.95,
                    'auto_approve': False,
                    'auto_apply': False
                },
                'is_system_template': True
            }
        ]

        for t in templates:
            AutomationLibraryTemplate.objects.update_or_create(
                template_name=t['template_name'],
                is_system_template=True,
                defaults=t
            )
            self.stdout.write(self.style.SUCCESS(f"Seeded template: {t['template_name']}"))
