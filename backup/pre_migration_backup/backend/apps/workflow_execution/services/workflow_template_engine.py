from __future__ import annotations

from copy import deepcopy
from typing import Any

from django.db.models import Avg, Count
from django.utils import timezone

from apps.orchestration_center.models.workflow import Workflow
from apps.workflow_execution.models import (
    WorkflowTemplate,
    WorkflowTemplateRating,
    WorkflowTemplateUsage,
    WorkflowTemplateVersion,
)
from apps.workflow_execution.services.workflow_versioning_engine import WorkflowVersioningEngine


class WorkflowTemplateEngine:
    SYSTEM_DEFAULT_TEMPLATES: list[dict[str, Any]] = [
        {
            'name': 'Standard Hiring Workflow',
            'description': 'Default full-cycle hiring flow.',
            'category': 'standard_hiring',
            'template_type': 'system',
            'visibility': 'public',
            'metadata': {
                'definition': {
                    'stages': [
                        {'key': 'job_created', 'name': 'Job Created'},
                        {'key': 'candidate_review', 'name': 'Candidate Review'},
                        {'key': 'interviews', 'name': 'Interviews'},
                        {'key': 'offer', 'name': 'Offer'},
                        {'key': 'onboarding', 'name': 'Onboarding'},
                    ],
                    'transitions': [
                        {'from': 'job_created', 'to': 'candidate_review'},
                        {'from': 'candidate_review', 'to': 'interviews'},
                        {'from': 'interviews', 'to': 'offer'},
                        {'from': 'offer', 'to': 'onboarding'},
                    ],
                }
            },
        },
        {
            'name': 'High Volume Hiring',
            'description': 'Parallel screening and fast pipeline progression.',
            'category': 'high_volume_hiring',
            'template_type': 'system',
            'visibility': 'public',
            'metadata': {'definition': {'stages': [], 'transitions': []}},
        },
        {
            'name': 'Executive Hiring',
            'description': 'Multi-step approvals with executive panel checkpoints.',
            'category': 'executive_hiring',
            'template_type': 'system',
            'visibility': 'public',
            'metadata': {'definition': {'stages': [], 'transitions': []}},
        },
        {
            'name': 'Campus Hiring',
            'description': 'Campus event to offer conversion pipeline.',
            'category': 'campus_hiring',
            'template_type': 'system',
            'visibility': 'public',
            'metadata': {'definition': {'stages': [], 'transitions': []}},
        },
        {
            'name': 'Agency Hiring',
            'description': 'Agency-led sourcing with client-side handoff stages.',
            'category': 'agency_hiring',
            'template_type': 'system',
            'visibility': 'public',
            'metadata': {'definition': {'stages': [], 'transitions': []}, 'future_support': True},
        },
        {
            'name': 'Contract Hiring',
            'description': 'Contract hiring with compliance and onboarding checkpoints.',
            'category': 'contract_hiring',
            'template_type': 'system',
            'visibility': 'public',
            'metadata': {'definition': {'stages': [], 'transitions': []}},
        },
    ]

    @staticmethod
    def _normalize_snapshot(snapshot: dict[str, Any] | None) -> dict[str, Any]:
        data = deepcopy(snapshot or {})
        for key in (
            'stages',
            'edges',
            'transitions',
            'conditions',
            'actions',
            'routing_rules',
            'sla_rules',
            'notification_rules',
            'human_task_rules',
        ):
            data.setdefault(key, [])
        return data

    @staticmethod
    def _next_template_version_number(template: WorkflowTemplate) -> int:
        latest = template.versions.order_by('-version_number').first()
        return (latest.version_number + 1) if latest else 1

    @staticmethod
    def _create_template_version(
        *,
        template: WorkflowTemplate,
        config_snapshot: dict[str, Any],
        created_by=None,
        is_active: bool = True,
    ) -> WorkflowTemplateVersion:
        return WorkflowTemplateVersion.objects.create(
            tenant_id=template.tenant_id,
            template=template,
            version_number=WorkflowTemplateEngine._next_template_version_number(template),
            config_snapshot=WorkflowTemplateEngine._normalize_snapshot(config_snapshot),
            created_by=created_by,
            is_active=is_active,
        )

    @staticmethod
    def create_template(
        *,
        name: str,
        description: str = '',
        category: str = 'custom',
        template_type: str = 'custom',
        visibility: str = 'private',
        tenant_id=None,
        created_by=None,
        config_snapshot: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowTemplate:
        template = WorkflowTemplate.objects.create(
            tenant_id=tenant_id,
            name=name,
            description=description,
            category=category,
            template_type=template_type,
            visibility=visibility,
            created_by=created_by,
            metadata=metadata or {},
            is_active=True,
        )
        WorkflowTemplateEngine._create_template_version(
            template=template,
            config_snapshot=config_snapshot or {},
            created_by=created_by,
            is_active=True,
        )
        return template

    @staticmethod
    def update_template(
        *,
        template: WorkflowTemplate,
        name: str | None = None,
        description: str | None = None,
        category: str | None = None,
        visibility: str | None = None,
        is_active: bool | None = None,
        metadata: dict[str, Any] | None = None,
        config_snapshot: dict[str, Any] | None = None,
        created_by=None,
    ) -> WorkflowTemplate:
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if category is not None:
            template.category = category
        if visibility is not None:
            template.visibility = visibility
        if is_active is not None:
            template.is_active = is_active
        if metadata is not None:
            template.metadata = metadata
        template.save(update_fields=['name', 'description', 'category', 'visibility', 'is_active', 'metadata', 'updated_at'])

        if config_snapshot is not None:
            WorkflowTemplateEngine._create_template_version(
                template=template,
                config_snapshot=config_snapshot,
                created_by=created_by,
                is_active=True,
            )
        return template

    @staticmethod
    def clone_template(
        *,
        template: WorkflowTemplate,
        created_by=None,
        tenant_id=None,
        name: str | None = None,
    ) -> WorkflowTemplate:
        latest = template.versions.order_by('-version_number').first()
        clone_name = name or f'{template.name} (Clone)'
        cloned = WorkflowTemplateEngine.create_template(
            name=clone_name,
            description=template.description,
            category=template.category,
            template_type='custom' if template.template_type == 'system' else template.template_type,
            visibility='private' if template.visibility == 'public' else template.visibility,
            tenant_id=tenant_id if tenant_id is not None else template.tenant_id,
            created_by=created_by,
            config_snapshot=(latest.config_snapshot if latest else {}),
            metadata=deepcopy(template.metadata or {}),
        )
        cloned.metadata = {**(cloned.metadata or {}), 'cloned_from_template_id': str(template.id)}
        cloned.save(update_fields=['metadata', 'updated_at'])
        return cloned

    @staticmethod
    def apply_template(
        *,
        template: WorkflowTemplate,
        tenant_id,
        workflow_name: str | None = None,
        workflow_description: str = '',
        trigger_event: str = 'manual',
        used_by=None,
    ) -> Workflow:
        workflow = Workflow.objects.create(
            tenant_id=tenant_id,
            name=workflow_name or template.name,
            description=workflow_description or template.description,
            trigger_event=trigger_event,
            status='active',
            is_active=True,
        )

        WorkflowTemplateUsage.objects.create(
            tenant_id=tenant_id,
            template=template,
            workflow_id=workflow.id,
            used_by=used_by,
            created_by=used_by,
            metadata={'applied_from_template_version': str(template.versions.order_by('-version_number').first().id) if template.versions.exists() else ''},
        )

        draft = WorkflowVersioningEngine.create_draft(
            workflow_id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            builder_mode='advanced',
            created_by=used_by,
        )

        latest_template_version = template.versions.order_by('-version_number').first()
        if latest_template_version and latest_template_version.config_snapshot:
            WorkflowVersioningEngine.save_draft_snapshot(
                draft=draft,
                config_snapshot=latest_template_version.config_snapshot,
                ready_for_publish=True,
                changed_by=used_by,
            )
        WorkflowVersioningEngine.publish_draft(
            draft=draft,
            notes=f'Published from template {template.name}',
            changed_by=used_by,
        )
        return workflow

    @staticmethod
    def publish_template(*, template: WorkflowTemplate, visibility: str | None = None) -> WorkflowTemplate:
        if visibility:
            template.visibility = visibility
        template.is_active = True
        metadata = dict(template.metadata or {})
        metadata['published_at'] = timezone.now().isoformat()
        template.metadata = metadata
        template.save(update_fields=['visibility', 'is_active', 'metadata', 'updated_at'])
        return template

    @staticmethod
    def archive_template(*, template: WorkflowTemplate) -> WorkflowTemplate:
        template.is_active = False
        template.save(update_fields=['is_active', 'updated_at'])
        return template

    @staticmethod
    def export_template(*, template: WorkflowTemplate) -> dict[str, Any]:
        latest = template.versions.order_by('-version_number').first()
        return {
            'template': {
                'id': str(template.id),
                'name': template.name,
                'description': template.description,
                'category': template.category,
                'template_type': template.template_type,
                'visibility': template.visibility,
                'is_active': template.is_active,
                'metadata': template.metadata or {},
            },
            'version': {
                'id': str(latest.id) if latest else None,
                'version_number': latest.version_number if latest else 0,
                'config_snapshot': latest.config_snapshot if latest else {},
            },
        }

    @staticmethod
    def import_template(
        *,
        payload: dict[str, Any],
        tenant_id=None,
        created_by=None,
    ) -> WorkflowTemplate:
        template_block = payload.get('template') or {}
        version_block = payload.get('version') or {}
        config_snapshot = version_block.get('config_snapshot') or template_block.get('config_snapshot') or {}
        template = WorkflowTemplateEngine.create_template(
            name=template_block.get('name', 'Imported Template'),
            description=template_block.get('description', ''),
            category=template_block.get('category', 'custom'),
            template_type=template_block.get('template_type', 'custom'),
            visibility=template_block.get('visibility', 'private'),
            tenant_id=tenant_id,
            created_by=created_by,
            config_snapshot=config_snapshot,
            metadata=template_block.get('metadata', {}),
        )
        return template

    @staticmethod
    def rate_template(
        *,
        template: WorkflowTemplate,
        rating: int,
        review: str = '',
        created_by=None,
        tenant_id=None,
    ) -> WorkflowTemplateRating:
        rating_record = WorkflowTemplateRating.objects.create(
            tenant_id=tenant_id if tenant_id is not None else template.tenant_id,
            template=template,
            rating=rating,
            review=review,
            created_by=created_by,
        )
        aggregate = template.ratings.aggregate(avg_rating=Avg('rating'), count=Count('id'))
        template.metadata = {
            **(template.metadata or {}),
            'average_rating': float(aggregate.get('avg_rating') or 0.0),
            'ratings_count': int(aggregate.get('count') or 0),
        }
        template.save(update_fields=['metadata', 'updated_at'])
        return rating_record

    @staticmethod
    def ensure_system_templates() -> list[WorkflowTemplate]:
        created_or_existing: list[WorkflowTemplate] = []
        for payload in WorkflowTemplateEngine.SYSTEM_DEFAULT_TEMPLATES:
            template, created = WorkflowTemplate.objects.get_or_create(
                name=payload['name'],
                template_type='system',
                defaults={
                    'description': payload.get('description', ''),
                    'category': payload.get('category', 'custom'),
                    'visibility': payload.get('visibility', 'public'),
                    'is_active': True,
                    'metadata': payload.get('metadata', {}),
                },
            )
            if created:
                WorkflowTemplateEngine._create_template_version(
                    template=template,
                    config_snapshot=payload.get('metadata', {}).get('definition', {}),
                    created_by=template.created_by,
                    is_active=True,
                )
            created_or_existing.append(template)
        return created_or_existing


# Function-style exports required by prompt contract.
create_template = WorkflowTemplateEngine.create_template
update_template = WorkflowTemplateEngine.update_template
clone_template = WorkflowTemplateEngine.clone_template
apply_template = WorkflowTemplateEngine.apply_template
publish_template = WorkflowTemplateEngine.publish_template
archive_template = WorkflowTemplateEngine.archive_template
export_template = WorkflowTemplateEngine.export_template
import_template = WorkflowTemplateEngine.import_template
rate_template = WorkflowTemplateEngine.rate_template
