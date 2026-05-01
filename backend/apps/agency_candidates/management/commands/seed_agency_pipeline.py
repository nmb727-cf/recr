from django.core.management.base import BaseCommand
from apps.agency_candidates.models import AgencyCandidatePipelineRegistry


class Command(BaseCommand):
    help = 'Seed default agency candidate pipeline stages'

    def handle(self, *args, **options):
        default_stages = [
            ('new_lead', 'New Lead', 1),
            ('contacted', 'Contacted', 2),
            ('screened', 'Screened', 3),
            ('qualified', 'Qualified', 4),
            ('ready_to_submit', 'Ready to Submit', 5),
            ('submitted', 'Submitted', 6),
            ('placed', 'Placed', 7),
            ('dormant', 'Dormant', 8),
        ]

        for key, label, order in default_stages:
            stage, created = AgencyCandidatePipelineRegistry.objects.get_or_create(
                tenant_id=None, # System default
                stage_key=key,
                defaults={
                    'stage_label': label,
                    'order': order,
                    'is_system': True,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created stage: {label}'))
            else:
                self.stdout.write(f'Stage already exists: {label}')
