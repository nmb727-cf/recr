from __future__ import annotations

from copy import deepcopy
from typing import Any

from django.utils import timezone

from apps.orchestration_center.models.workflow import WorkflowNode, WorkflowEdge
from apps.workflow_execution.models import (
    WorkflowActionDefinition,
    WorkflowApprovalRule,
    WorkflowConditionRule,
    WorkflowDraft,
    WorkflowNotificationRule,
    WorkflowRoutingRule,
    WorkflowStageSLA,
    WorkflowStageTransition,
    WorkflowVersion,
    WorkflowVersionChangeLog,
    WorkflowVersionComparison,
)


class WorkflowVersioningEngine:
    @staticmethod
    def _serialize_queryset(qs, fields: list[str]) -> list[dict[str, Any]]:
        rows = []
        for row in qs.values(*fields):
            normalized = {}
            for key, value in row.items():
                normalized[key] = str(value) if hasattr(value, 'hex') else value
            rows.append(normalized)
        return rows

    @staticmethod
    def _build_workflow_snapshot(workflow_id) -> dict[str, Any]:
        snapshot = {
            'workflow_id': str(workflow_id),
            'captured_at': timezone.now().isoformat(),
            'stages': WorkflowVersioningEngine._serialize_queryset(
                WorkflowNode.objects.filter(workflow_id=workflow_id).order_by('id'),
                ['id', 'node_type', 'config'],
            ),
            'edges': WorkflowVersioningEngine._serialize_queryset(
                WorkflowEdge.objects.filter(workflow_id=workflow_id).order_by('id'),
                ['id', 'source_node_id', 'target_node_id', 'condition'],
            ),
            'transitions': WorkflowVersioningEngine._serialize_queryset(
                WorkflowStageTransition.objects.filter(workflow_id=workflow_id).order_by('priority', 'created_at'),
                ['id', 'from_stage_id', 'to_stage_id', 'transition_type', 'condition_config', 'priority', 'label', 'is_active'],
            ),
            'conditions': WorkflowVersioningEngine._serialize_queryset(
                WorkflowConditionRule.objects.filter(workflow_id=workflow_id).order_by('priority', 'created_at'),
                ['id', 'stage_id', 'rule_name', 'rule_group', 'condition_type', 'field_name', 'operator', 'expected_value', 'logical_join', 'priority', 'is_active'],
            ),
            'actions': WorkflowVersioningEngine._serialize_queryset(
                WorkflowActionDefinition.objects.filter(workflow_id=workflow_id).order_by('execution_order', 'created_at'),
                ['id', 'stage_id', 'action_name', 'action_type', 'action_config', 'execution_order', 'run_mode', 'is_active'],
            ),
            'routing_rules': WorkflowVersioningEngine._serialize_queryset(
                WorkflowRoutingRule.objects.filter(workflow_id=workflow_id).order_by('priority', 'created_at'),
                ['id', 'stage_id', 'condition_config', 'route_to_entity_type', 'route_to_actor_type', 'route_config', 'priority', 'label', 'is_active'],
            ),
            'sla_rules': WorkflowVersioningEngine._serialize_queryset(
                WorkflowStageSLA.objects.filter(workflow_id=workflow_id).order_by('created_at'),
                ['id', 'stage_id', 'sla_duration', 'warning_duration', 'escalation_duration', 'escalation_role', 'escalation_user', 'is_active'],
            ),
            'notification_rules': WorkflowVersioningEngine._serialize_queryset(
                WorkflowNotificationRule.objects.filter(workflow_id=workflow_id).order_by('created_at'),
                ['id', 'stage_id', 'trigger_type', 'recipient_type', 'channel', 'template_key', 'is_active'],
            ),
            'human_task_rules': WorkflowVersioningEngine._serialize_queryset(
                WorkflowApprovalRule.objects.filter(workflow_id=workflow_id).order_by('created_at'),
                ['id', 'stage_id', 'approval_type', 'required_approvals', 'approval_role', 'escalation_role', 'timeout_hours', 'is_active'],
            ),
        }
        return snapshot

    @staticmethod
    def _normalize_for_compare(items: list[dict[str, Any]]):
        by_id: dict[str, dict[str, Any]] = {}
        for item in items or []:
            item_copy = deepcopy(item)
            key = str(item_copy.get('id') or item_copy.get('key') or hash(str(item_copy)))
            by_id[key] = item_copy
        return by_id

    @staticmethod
    def _diff_component(from_items: list[dict[str, Any]], to_items: list[dict[str, Any]]) -> dict[str, Any]:
        from_map = WorkflowVersioningEngine._normalize_for_compare(from_items)
        to_map = WorkflowVersioningEngine._normalize_for_compare(to_items)

        from_keys = set(from_map.keys())
        to_keys = set(to_map.keys())

        added = [to_map[k] for k in sorted(to_keys - from_keys)]
        removed = [from_map[k] for k in sorted(from_keys - to_keys)]
        changed = []
        for key in sorted(from_keys & to_keys):
            if from_map[key] != to_map[key]:
                changed.append({'id': key, 'from': from_map[key], 'to': to_map[key]})
        return {
            'added': added,
            'removed': removed,
            'changed': changed,
        }

    @staticmethod
    def _next_version_number(workflow_id) -> int:
        latest = WorkflowVersion.objects.filter(workflow_id=workflow_id).order_by('-version_number').first()
        return (latest.version_number + 1) if latest else 1

    @staticmethod
    def log_version_change(*, workflow_id, version=None, change_type: str, changed_by=None, change_summary: str = '', metadata=None):
        return WorkflowVersionChangeLog.objects.create(
            tenant_id=getattr(version, 'tenant_id', None),
            workflow_id=workflow_id,
            version=version,
            change_type=change_type,
            changed_by=changed_by,
            change_summary=change_summary,
            metadata=metadata or {},
        )

    @staticmethod
    def create_draft(*, workflow_id, name: str = '', description: str = '', builder_mode: str = 'guided', created_by=None):
        existing = WorkflowDraft.objects.filter(
            workflow_id=workflow_id,
            status__in=['editing', 'ready_for_publish'],
        ).order_by('-updated_at').first()
        if existing:
            return existing

        snapshot = WorkflowVersioningEngine._build_workflow_snapshot(workflow_id)
        version = WorkflowVersion.objects.create(
            workflow_id=workflow_id,
            version_number=WorkflowVersioningEngine._next_version_number(workflow_id),
            status='draft',
            created_by=created_by,
            metadata={'config_snapshot': snapshot},
        )
        draft = WorkflowDraft.objects.create(
            workflow_id=workflow_id,
            version=version,
            name=name,
            description=description,
            config_snapshot=snapshot,
            builder_mode=builder_mode,
            status='editing',
            created_by=created_by,
        )
        WorkflowVersioningEngine.log_version_change(
            workflow_id=workflow_id,
            version=version,
            change_type='created',
            changed_by=created_by,
            change_summary='Draft created',
            metadata={'draft_id': str(draft.id)},
        )
        return draft

    @staticmethod
    def update_draft(*, draft: WorkflowDraft, name=None, description=None, builder_mode=None, status=None):
        if name is not None:
            draft.name = name
        if description is not None:
            draft.description = description
        if builder_mode is not None:
            draft.builder_mode = builder_mode
        if status is not None:
            draft.status = status
        draft.save(update_fields=['name', 'description', 'builder_mode', 'status', 'updated_at'])
        WorkflowVersioningEngine.log_version_change(
            workflow_id=draft.workflow_id,
            version=draft.version,
            change_type='edited',
            changed_by=draft.created_by,
            change_summary='Draft metadata updated',
            metadata={'draft_id': str(draft.id)},
        )
        return draft

    @staticmethod
    def save_draft_snapshot(*, draft: WorkflowDraft, config_snapshot=None, ready_for_publish: bool = False, changed_by=None):
        snapshot = config_snapshot or WorkflowVersioningEngine._build_workflow_snapshot(draft.workflow_id)
        draft.config_snapshot = snapshot
        if ready_for_publish:
            draft.status = 'ready_for_publish'
        draft.save(update_fields=['config_snapshot', 'status', 'updated_at'])
        if draft.version:
            draft.version.metadata = {**(draft.version.metadata or {}), 'config_snapshot': snapshot}
            draft.version.save(update_fields=['metadata', 'updated_at'])

        WorkflowVersioningEngine.log_version_change(
            workflow_id=draft.workflow_id,
            version=draft.version,
            change_type='edited',
            changed_by=changed_by,
            change_summary='Draft snapshot saved',
            metadata={'draft_id': str(draft.id), 'ready_for_publish': ready_for_publish},
        )
        return draft

    @staticmethod
    def publish_draft(*, draft: WorkflowDraft, notes: str = '', changed_by=None):
        snapshot = draft.config_snapshot or WorkflowVersioningEngine._build_workflow_snapshot(draft.workflow_id)

        WorkflowVersion.objects.filter(workflow_id=draft.workflow_id, status='published').update(status='archived')

        version = draft.version
        if version is None:
            version = WorkflowVersion.objects.create(
                workflow_id=draft.workflow_id,
                version_number=WorkflowVersioningEngine._next_version_number(draft.workflow_id),
                status='draft',
                created_by=draft.created_by,
            )
            draft.version = version

        version.status = 'published'
        version.published_at = timezone.now()
        version.notes = notes
        version.metadata = {**(version.metadata or {}), 'config_snapshot': snapshot}
        version.save(update_fields=['status', 'published_at', 'notes', 'metadata', 'updated_at'])

        draft.status = 'published'
        draft.save(update_fields=['version', 'status', 'updated_at'])

        WorkflowVersioningEngine.log_version_change(
            workflow_id=draft.workflow_id,
            version=version,
            change_type='published',
            changed_by=changed_by,
            change_summary='Draft published',
            metadata={'draft_id': str(draft.id)},
        )
        return version

    @staticmethod
    def archive_version(*, version: WorkflowVersion, changed_by=None, summary='Version archived'):
        version.status = 'archived'
        version.save(update_fields=['status', 'updated_at'])
        WorkflowVersioningEngine.log_version_change(
            workflow_id=version.workflow_id,
            version=version,
            change_type='edited',
            changed_by=changed_by,
            change_summary=summary,
        )
        return version

    @staticmethod
    def rollback_to_version(*, workflow_id, version_id, changed_by=None):
        target = WorkflowVersion.objects.filter(workflow_id=workflow_id, id=version_id).first()
        if target is None:
            return None

        WorkflowVersion.objects.filter(workflow_id=workflow_id, status='published').exclude(id=target.id).update(status='archived')

        target.status = 'published'
        target.published_at = timezone.now()
        target.metadata = {**(target.metadata or {}), 'rollback_activated_at': timezone.now().isoformat()}
        target.save(update_fields=['status', 'published_at', 'metadata', 'updated_at'])

        WorkflowVersioningEngine.log_version_change(
            workflow_id=workflow_id,
            version=target,
            change_type='rolled_back',
            changed_by=changed_by,
            change_summary='Rolled back to selected version',
            metadata={'target_version_id': str(target.id)},
        )
        return target

    @staticmethod
    def clone_version(*, workflow_id, version_id, changed_by=None):
        source = WorkflowVersion.objects.filter(workflow_id=workflow_id, id=version_id).first()
        if source is None:
            return None

        cloned = WorkflowVersion.objects.create(
            workflow_id=workflow_id,
            version_number=WorkflowVersioningEngine._next_version_number(workflow_id),
            status='draft',
            created_by=changed_by,
            notes=f'Cloned from version {source.version_number}',
            metadata=deepcopy(source.metadata or {}),
        )
        draft = WorkflowDraft.objects.create(
            workflow_id=workflow_id,
            version=cloned,
            name=f'Clone of v{source.version_number}',
            description='Cloned draft',
            config_snapshot=deepcopy((source.metadata or {}).get('config_snapshot') or {}),
            builder_mode='advanced',
            status='editing',
            created_by=changed_by,
        )
        WorkflowVersioningEngine.log_version_change(
            workflow_id=workflow_id,
            version=cloned,
            change_type='cloned',
            changed_by=changed_by,
            change_summary='Version cloned into editable draft',
            metadata={'source_version_id': str(source.id), 'draft_id': str(draft.id)},
        )
        return draft

    @staticmethod
    def compare_versions(*, workflow_id, from_version_id, to_version_id):
        from_version = WorkflowVersion.objects.filter(workflow_id=workflow_id, id=from_version_id).first()
        to_version = WorkflowVersion.objects.filter(workflow_id=workflow_id, id=to_version_id).first()
        if from_version is None or to_version is None:
            return None

        from_snapshot = deepcopy((from_version.metadata or {}).get('config_snapshot') or {})
        to_snapshot = deepcopy((to_version.metadata or {}).get('config_snapshot') or {})

        if not from_snapshot:
            from_snapshot = WorkflowVersioningEngine._build_workflow_snapshot(workflow_id)
        if not to_snapshot:
            to_snapshot = WorkflowVersioningEngine._build_workflow_snapshot(workflow_id)

        keys = [
            'stages',
            'transitions',
            'conditions',
            'actions',
            'routing_rules',
            'sla_rules',
            'notification_rules',
            'human_task_rules',
        ]
        result = {}
        for key in keys:
            result[key] = WorkflowVersioningEngine._diff_component(
                from_snapshot.get(key) or [],
                to_snapshot.get(key) or [],
            )

        comparison = WorkflowVersionComparison.objects.create(
            workflow_id=workflow_id,
            from_version=from_version,
            to_version=to_version,
            comparison_result=result,
        )
        return comparison

    @staticmethod
    def discard_draft(*, draft: WorkflowDraft, changed_by=None):
        draft.status = 'discarded'
        draft.save(update_fields=['status', 'updated_at'])
        if draft.version and draft.version.status == 'draft':
            draft.version.status = 'archived'
            draft.version.save(update_fields=['status', 'updated_at'])
        WorkflowVersioningEngine.log_version_change(
            workflow_id=draft.workflow_id,
            version=draft.version,
            change_type='discarded',
            changed_by=changed_by,
            change_summary='Draft discarded',
            metadata={'draft_id': str(draft.id)},
        )
        return draft

    @staticmethod
    def get_latest_published_version(workflow_id):
        return WorkflowVersion.objects.filter(workflow_id=workflow_id, status='published').order_by('-version_number').first()


# Function-level exports requested by prompt contract.
create_draft = WorkflowVersioningEngine.create_draft
update_draft = WorkflowVersioningEngine.update_draft
save_draft_snapshot = WorkflowVersioningEngine.save_draft_snapshot
publish_draft = WorkflowVersioningEngine.publish_draft
archive_version = WorkflowVersioningEngine.archive_version
rollback_to_version = WorkflowVersioningEngine.rollback_to_version
clone_version = WorkflowVersioningEngine.clone_version
compare_versions = WorkflowVersioningEngine.compare_versions
log_version_change = WorkflowVersioningEngine.log_version_change
