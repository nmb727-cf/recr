from django.core.management.base import BaseCommand

from apps.workflow_execution.services.workflow_template_engine import WorkflowTemplateEngine


class Command(BaseCommand):
    help = 'Seed system workflow templates for template library.'

    def handle(self, *args, **options):
        templates = WorkflowTemplateEngine.ensure_system_templates()
        self.stdout.write(
            self.style.SUCCESS(f'Workflow templates available: {len(templates)}')
        )
