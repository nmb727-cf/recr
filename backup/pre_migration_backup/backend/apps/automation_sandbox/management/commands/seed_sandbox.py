from django.core.management.base import BaseCommand
from apps.automation_sandbox.models import WorkflowSandboxScenario

class Command(BaseCommand):
    help = 'Seed initial system sandbox scenarios'

    def handle(self, *args, **options):
        scenarios = [
            {
                'name': 'Candidate Applied — Standard',
                'description': 'Typical candidate application event with basic profile data.',
                'module_scope': 'candidates',
                'trigger_event': 'candidate_applied',
                'scenario_payload': {
                    'candidate_name': 'John Doe',
                    'job_title': 'Senior Engineer',
                    'source': 'LinkedIn',
                    'score': 85
                },
                'is_system_scenario': True
            },
            {
                'name': 'Interview Completed — High Score',
                'description': 'Simulation of a positive interview outcome.',
                'module_scope': 'interviews',
                'trigger_event': 'interview_completed',
                'scenario_payload': {
                    'candidate_name': 'Jane Smith',
                    'interview_type': 'Technical',
                    'average_score': 4.8,
                    'panel_recommendation': 'hire'
                },
                'is_system_scenario': True
            },
            {
                'name': 'Deadline Missed — Escalation',
                'description': 'Test case for SLA breach and escalation logic.',
                'module_scope': 'sla',
                'trigger_event': 'deadline_missed',
                'scenario_payload': {
                    'entity_type': 'task',
                    'delay_hours': 24,
                    'priority': 'high'
                },
                'is_system_scenario': True
            }
        ]

        for s_data in scenarios:
            obj, created = WorkflowSandboxScenario.objects.get_or_create(
                name=s_data['name'],
                defaults=s_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created scenario: {obj.name}"))
            else:
                self.stdout.write(f"Scenario already exists: {obj.name}")
