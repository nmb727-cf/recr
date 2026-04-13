from django.core.management.base import BaseCommand
from apps.automation_playbooks.models import AutomationPlaybook, PlaybookCategory

class Command(BaseCommand):
    help = 'Seed initial system playbooks'

    def handle(self, *args, **options):
        playbooks = [
            {
                'name': 'Candidate Follow-up Playbook',
                'description': 'Automates candidate follow-up after application, including recruiter reminders and escalation notifications.',
                'category': PlaybookCategory.CANDIDATE,
                'is_system_playbook': True,
                'version': '1.0.0'
            },
            {
                'name': 'Interview Coordination Playbook',
                'description': 'Handles interview scheduling reminders, panel feedback tasks, and interview SLA tracking.',
                'category': PlaybookCategory.INTERVIEW,
                'is_system_playbook': True,
                'version': '1.0.0'
            },
            {
                'name': 'Agency SLA Control Playbook',
                'description': 'Enforces acknowledgment SLAs, triggers reminders, and handles breach escalations for agency submissions.',
                'category': PlaybookCategory.SLA,
                'is_system_playbook': True,
                'version': '1.0.0'
            },
            {
                'name': 'Fast Hiring Playbook',
                'description': 'Accelerates hiring via shortlist follow-ups, interview scheduling SLAs, and automated offer trigger chains.',
                'category': PlaybookCategory.CROSS_MODULE,
                'is_system_playbook': True,
                'version': '1.0.0'
            }
        ]

        for p_data in playbooks:
            pb, created = AutomationPlaybook.objects.get_or_create(
                name=p_data['name'],
                defaults=p_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created playbook: {pb.name}"))
            else:
                self.stdout.write(f"Playbook already exists: {pb.name}")
