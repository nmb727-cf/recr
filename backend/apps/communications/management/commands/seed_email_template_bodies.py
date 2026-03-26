"""
Management command: seed_email_template_bodies

Applies canonical subject/body content to the 5 core business email templates.
Run once after initial tenant seeding, or after any reset.

Usage:
    python manage.py seed_email_template_bodies
"""

from django.core.management.base import BaseCommand

from apps.communications.email_templates.template_seed_bodies import apply_core_template_bodies


class Command(BaseCommand):
    help = 'Upsert body content into the 5 core business email templates.'

    def handle(self, *args, **options):
        updated = apply_core_template_bodies()
        if updated:
            self.stdout.write(self.style.SUCCESS(f'Updated templates: {", ".join(updated)}'))
        else:
            self.stdout.write(self.style.WARNING('No matching template rows found. Run seed_defaults_for_tenant first.'))
