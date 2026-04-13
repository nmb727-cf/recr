import re

from django.db import transaction
from django.utils import timezone

from apps.orchestration_center.constants.execution_statuses import PromptStatus, ValidationStatus
from apps.orchestration_center.models import PromptScope, PromptTemplate, PromptTestRun, PromptVersion
from apps.orchestration_center.services.provider_router import ProviderExecutionError, ProviderRouter


class SafePromptDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


class PromptRegistryService:
    PLACEHOLDER_PATTERN = re.compile(r'\{([^{}]+)\}')

    @staticmethod
    def get_active_prompt_version(tenant_id, module_scope, use_case_key):
        template = (
            PromptTemplate.objects.filter(
                tenant_id__in=[tenant_id, None],
                module_scope=module_scope,
                use_case_key=use_case_key,
                status__in=[PromptStatus.ACTIVE, PromptStatus.APPROVED],
                is_deleted=False,
            )
            .order_by('-tenant_id')
            .first()
        )
        if not template:
            return None
        return (
            PromptVersion.objects.filter(prompt_template=template, status__in=[PromptStatus.ACTIVE, PromptStatus.APPROVED], is_deleted=False)
            .order_by('-version_number')
            .first()
        )

    @staticmethod
    @transaction.atomic
    def create_template(*, tenant_id, created_by, template_data):
        scopes = template_data.pop('scopes', [])
        initial_version = template_data.pop('initial_version', None)
        template = PromptTemplate.objects.create(
            tenant_id=tenant_id,
            created_by=created_by,
            status=PromptStatus.DRAFT,
            **template_data,
        )
        PromptRegistryService._replace_scopes(
            prompt_template=template,
            tenant_id=tenant_id,
            created_by=created_by,
            scopes=scopes,
        )
        if initial_version:
            PromptRegistryService.create_version(
                tenant_id=tenant_id,
                created_by=created_by,
                prompt_template=template,
                version_data=initial_version,
            )
        return template

    @staticmethod
    @transaction.atomic
    def update_template(*, template, template_data):
        scopes = template_data.pop('scopes', None)
        for field, value in template_data.items():
            setattr(template, field, value)
        template.save()
        if scopes is not None:
            PromptRegistryService._replace_scopes(
                prompt_template=template,
                tenant_id=template.tenant_id,
                created_by=template.created_by,
                scopes=scopes,
            )
        return template

    @staticmethod
    @transaction.atomic
    def create_version(*, tenant_id, created_by, prompt_template, version_data):
        next_version = (prompt_template.versions.order_by('-version_number').values_list('version_number', flat=True).first() or 0) + 1
        version = PromptVersion.objects.create(
            tenant_id=tenant_id,
            created_by=created_by,
            prompt_template=prompt_template,
            version_number=version_data.get('version_number') or next_version,
            system_prompt=version_data['system_prompt'],
            user_prompt_template=version_data['user_prompt_template'],
            variables_schema_json=version_data.get('variables_schema_json', {}),
            expected_output_schema_json=version_data.get('expected_output_schema_json', {}),
            validation_rules_json=version_data.get('validation_rules_json', {}),
            fallback_version_id=version_data.get('fallback_version_id'),
            approval_required=version_data.get('approval_required', prompt_template.approval_required),
            activation_notes=version_data.get('activation_notes', ''),
            diff_notes=version_data.get('diff_notes', ''),
            status=version_data.get('status', PromptStatus.DRAFT),
        )
        return version

    @staticmethod
    @transaction.atomic
    def approve_version(*, version, approver_id, activate=False):
        if version.status == PromptStatus.ARCHIVED:
            raise ValueError('Archived prompt versions cannot be approved.')
        version.status = PromptStatus.APPROVED
        version.approved_by_id = approver_id
        version.approved_at = timezone.now()
        version.save(update_fields=['status', 'approved_by_id', 'approved_at', 'updated_at'])
        template = version.prompt_template
        if activate:
            previous_active_id = template.active_version_id
            if previous_active_id and previous_active_id != version.id:
                PromptVersion.objects.filter(
                    prompt_template=template,
                    pk=previous_active_id,
                    status=PromptStatus.ACTIVE,
                ).update(status=PromptStatus.APPROVED)
            template.active_version_id = version.id
            template.status = PromptStatus.ACTIVE
            template.save(update_fields=['active_version_id', 'status', 'updated_at'])
            version.status = PromptStatus.ACTIVE
            version.save(update_fields=['status', 'updated_at'])
        return version

    @staticmethod
    @transaction.atomic
    def archive_template(*, template):
        if template.active_version_id:
            raise ValueError('Active prompt templates cannot be archived until the active version is changed.')
        template.status = PromptStatus.ARCHIVED
        template.save(update_fields=['status', 'updated_at'])
        return template

    @staticmethod
    def create_test_run(*, tenant_id, created_by, prompt_version, test_input_json):
        test_run = PromptTestRun.objects.create(
            tenant_id=tenant_id,
            created_by=created_by,
            prompt_version=prompt_version,
            test_input_json=test_input_json or {},
            executed_by_id=created_by,
            run_status=ValidationStatus.NOT_CHECKED,
            validation_status=ValidationStatus.NOT_CHECKED,
        )
        try:
            rendered_prompt = PromptRegistryService.render_prompt(
                prompt_version=prompt_version,
                context_snapshot=test_input_json or {},
            )
            route = ProviderRouter.resolve(
                tenant_id=tenant_id,
                module_scope=prompt_version.prompt_template.module_scope,
                use_case_key=prompt_version.prompt_template.use_case_key,
            )
            execution = ProviderRouter.execute_with_fallback(
                route=route,
                prompt_version=prompt_version,
                rendered_prompt=rendered_prompt,
                context_snapshot=test_input_json or {},
            )
            test_run.raw_response_ref = execution.get('raw_response_ref', '')
            test_run.normalized_output_json = execution['normalized_output_json']
            test_run.validation_status = ValidationStatus.VALID if execution['validation_passed'] else ValidationStatus.INVALID
            test_run.run_status = ValidationStatus.PASSED if execution['validation_passed'] else ValidationStatus.FAILED
            test_run.save(
                update_fields=[
                    'raw_response_ref',
                    'normalized_output_json',
                    'validation_status',
                    'run_status',
                    'updated_at',
                ]
            )
        except ProviderExecutionError:
            test_run.run_status = ValidationStatus.FAILED
            test_run.validation_status = ValidationStatus.NOT_CHECKED
            test_run.notes = 'Prompt test execution failed.'
            test_run.save(update_fields=['run_status', 'validation_status', 'notes', 'updated_at'])
        return test_run

    @staticmethod
    def resolve_prompt_version(*, tenant_id, module_scope, use_case_key, request_prompt_version=None):
        if request_prompt_version:
            return request_prompt_version
        return PromptRegistryService.get_active_prompt_version(
            tenant_id=tenant_id,
            module_scope=module_scope,
            use_case_key=use_case_key,
        )

    @staticmethod
    def render_prompt(*, prompt_version, context_snapshot):
        context = SafePromptDict(PromptRegistryService._flatten_context(context_snapshot or {}))
        system_prompt = PromptRegistryService._render_template(prompt_version.system_prompt, context)
        user_prompt = PromptRegistryService._render_template(prompt_version.user_prompt_template, context)
        return {
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
        }

    @staticmethod
    def _replace_scopes(*, prompt_template, tenant_id, created_by, scopes):
        prompt_template.scopes.all().delete()
        for item in scopes:
            PromptScope.objects.create(
                tenant_id=tenant_id,
                created_by=created_by,
                prompt_template=prompt_template,
                module_scope=item.get('module_scope', prompt_template.module_scope),
                entity_type=item.get('entity_type', ''),
                use_case_key=item.get('use_case_key', prompt_template.use_case_key),
                priority_order=item.get('priority_order', 100),
                is_active=item.get('is_active', True),
            )

    @staticmethod
    def _flatten_context(payload, prefix=''):
        flattened = {}
        if isinstance(payload, dict):
            for key, value in payload.items():
                composite = f'{prefix}{key}' if not prefix else f'{prefix}.{key}'
                if isinstance(value, dict):
                    flattened.update(PromptRegistryService._flatten_context(value, composite))
                else:
                    flattened[composite] = value
                    flattened[key] = value
        return flattened

    @staticmethod
    def _render_template(template, context):
        def replace(match):
            key = match.group(1).strip()
            return str(context.get(key, '{' + key + '}'))

        return PromptRegistryService.PLACEHOLDER_PATTERN.sub(replace, template)
