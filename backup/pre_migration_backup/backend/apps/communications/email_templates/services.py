import re
from typing import Any

from django.db import transaction
from django.template import Context, Template
from django.utils.text import slugify

from apps.communications.constants import (
    DEFAULT_BUSINESS_TEMPLATE_DEFINITIONS,
    DEFAULT_QUICK_REPLIES,
    DEFAULT_SYSTEM_TEMPLATE_DEFINITIONS,
)
from apps.communications.models import (
    EmailTemplateDefinition,
    EmailTemplateScope,
    EmailTemplateType,
    QuickReplyTemplate,
)


class EmailTemplateService:
    @staticmethod
    def render_template_string(template_str: str, variables: dict[str, Any]) -> str:
        if not template_str:
            return ''
        template = Template(template_str)
        return template.render(Context(variables))

    @staticmethod
    def extract_variables(content: str) -> list[str]:
        if not content:
            return []
        found = re.findall(r'{{\s*([a-zA-Z0-9_\.]+)\s*}}', content)
        return sorted(list(set(found)))

    @staticmethod
    def render_template(template: EmailTemplateDefinition, variables: dict[str, Any]) -> dict[str, str]:
        return {
            'subject': EmailTemplateService.render_template_string(template.subject_template, variables),
            'body_html': EmailTemplateService.render_template_string(template.body_html, variables),
            'body_text': EmailTemplateService.render_template_string(template.body_text, variables),
        }

    @staticmethod
    def render_quick_reply(template: QuickReplyTemplate, variables: dict[str, Any]) -> dict[str, str]:
        return {
            'subject': EmailTemplateService.render_template_string(template.subject_template or '', variables),
            'body_html': EmailTemplateService.render_template_string(template.body_html, variables),
            'body_text': EmailTemplateService.render_template_string(template.body_text, variables),
        }

    @staticmethod
    @transaction.atomic
    def duplicate_template(*, source: EmailTemplateDefinition, tenant_id: str, created_by: str | None) -> EmailTemplateDefinition:
        return EmailTemplateDefinition.objects.create(
            tenant_id=tenant_id,
            template_scope=EmailTemplateScope.TENANT_CUSTOM,
            template_type=source.template_type,
            channel=source.channel,
            name=f'{source.name} Copy',
            slug=f'{source.slug}-copy-{str(source.id)[:8]}',
            category=source.category,
            subject_template=source.subject_template,
            body_html=source.body_html,
            body_text=source.body_text,
            variables_schema_json=source.variables_schema_json,
            usage_context_json=source.usage_context_json,
            is_active=True,
            is_system_locked=False,
            language_code=source.language_code,
            version=1,
            parent_template=source,
            created_by=created_by,
        )

    @staticmethod
    @transaction.atomic
    def seed_defaults_for_tenant(tenant_id: str, user_id: str | None = None):
        for name, slug, category, subject in DEFAULT_SYSTEM_TEMPLATE_DEFINITIONS:
            EmailTemplateDefinition.objects.get_or_create(
                tenant_id=None,
                template_scope=EmailTemplateScope.SYSTEM_DEFAULT,
                template_type=EmailTemplateType.SYSTEM,
                slug=slug,
                language_code='en',
                version=1,
                defaults={
                    'name': name,
                    'category': category,
                    'subject_template': subject,
                    'body_html': '<p>{{ company_name|default:"TalentOS" }}</p>',
                    'body_text': '{{ company_name|default:"TalentOS" }}',
                    'variables_schema_json': {'variables': ['company_name']},
                    'is_system_locked': True,
                    'created_by': user_id,
                },
            )

        for name, slug, category in DEFAULT_BUSINESS_TEMPLATE_DEFINITIONS:
            EmailTemplateDefinition.objects.get_or_create(
                tenant_id=tenant_id,
                template_scope=EmailTemplateScope.TENANT_CUSTOM,
                template_type=EmailTemplateType.BUSINESS,
                slug=slug,
                language_code='en',
                version=1,
                defaults={
                    'name': name,
                    'category': category,
                    'subject_template': f'{name} - {{ candidate_name }}',
                    'body_html': '<p>Hello {{ candidate_name }},</p><p>{{ message_body }}</p>',
                    'body_text': 'Hello {{ candidate_name }}, {{ message_body }}',
                    'variables_schema_json': {
                        'variables': [
                            'candidate_name', 'first_name', 'last_name', 'company_name', 'agency_name',
                            'recruiter_name', 'recruiter_email', 'recruiter_phone', 'job_title',
                            'interview_date', 'interview_time', 'interview_location', 'meeting_link',
                            'offer_title', 'salary_range', 'portal_link', 'action_link', 'support_email',
                        ]
                    },
                    'created_by': user_id,
                },
            )

        for body_text, category in DEFAULT_QUICK_REPLIES:
            QuickReplyTemplate.objects.get_or_create(
                tenant_id=tenant_id,
                user_id=user_id,
                name=body_text[:70],
                category=category,
                defaults={
                    'body_text': body_text,
                    'body_html': f'<p>{body_text}</p>',
                    'subject_template': '',
                    'variables_schema_json': {},
                    'is_active': True,
                },
            )

    @staticmethod
    def safe_slug(name: str) -> str:
        return slugify(name).replace('-', '_')
