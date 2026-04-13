import uuid

from django.test import TestCase

from apps.workflow_execution.models import (
    WorkflowTemplate,
    WorkflowTemplateUsage,
)
from apps.workflow_execution.services.workflow_template_engine import WorkflowTemplateEngine


class TestWorkflowTemplateEngine(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

    def test_1_create_template_saved(self):
        template = WorkflowTemplateEngine.create_template(
            name='Template A',
            description='Template A Description',
            category='standard_hiring',
            template_type='company',
            visibility='organization',
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            config_snapshot={'stages': [{'key': 'review'}], 'transitions': []},
        )

        template.refresh_from_db()
        assert template.name == 'Template A'
        assert template.versions.count() == 1
        assert template.versions.first().version_number == 1

    def test_2_apply_template_creates_workflow(self):
        template = WorkflowTemplateEngine.create_template(
            name='Apply Me',
            category='standard_hiring',
            template_type='company',
            visibility='organization',
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            config_snapshot={'stages': [{'key': 'start'}], 'transitions': []},
        )

        workflow = WorkflowTemplateEngine.apply_template(
            template=template,
            tenant_id=self.tenant_id,
            workflow_name='Workflow from Template',
            trigger_event='job_created',
            used_by=self.user_id,
        )

        assert workflow is not None
        assert workflow.name == 'Workflow from Template'
        assert WorkflowTemplateUsage.objects.filter(template=template, workflow_id=workflow.id).exists()

    def test_3_clone_template_creates_new_template(self):
        source = WorkflowTemplateEngine.create_template(
            name='Source Template',
            category='campus_hiring',
            template_type='company',
            visibility='private',
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            config_snapshot={'stages': [{'key': 'screen'}], 'transitions': []},
        )

        cloned = WorkflowTemplateEngine.clone_template(
            template=source,
            created_by=self.user_id,
            tenant_id=self.tenant_id,
        )

        assert cloned.id != source.id
        assert cloned.versions.count() == 1
        assert cloned.versions.first().config_snapshot.get('stages') == [{'key': 'screen'}]

    def test_4_import_template_valid_template_created(self):
        payload = {
            'template': {
                'name': 'Imported Template',
                'description': 'Imported from JSON',
                'category': 'contract_hiring',
                'template_type': 'custom',
                'visibility': 'private',
            },
            'version': {
                'version_number': 1,
                'config_snapshot': {'stages': [{'key': 'offer'}], 'transitions': []},
            },
        }
        template = WorkflowTemplateEngine.import_template(
            payload=payload,
            tenant_id=self.tenant_id,
            created_by=self.user_id,
        )

        assert template.name == 'Imported Template'
        assert template.versions.count() == 1
        assert template.versions.first().config_snapshot.get('stages') == [{'key': 'offer'}]

    def test_5_export_template_json_generated(self):
        template = WorkflowTemplateEngine.create_template(
            name='Export Me',
            category='executive_hiring',
            template_type='custom',
            visibility='private',
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            config_snapshot={'stages': [{'key': 'approval'}], 'transitions': []},
        )

        exported = WorkflowTemplateEngine.export_template(template=template)
        assert isinstance(exported, dict)
        assert exported['template']['name'] == 'Export Me'
        assert 'config_snapshot' in exported['version']

    def test_6_system_templates_seeded(self):
        templates = WorkflowTemplateEngine.ensure_system_templates()
        assert len(templates) >= 6
        assert WorkflowTemplate.objects.filter(template_type='system').count() >= 6
