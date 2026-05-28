from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.pipeline.models import Application
from apps.interviews.models import Interview
from apps.jobs.models import JobRequisition, JobStage


@dataclass
class PolicyContext:
    mode: str
    strictness: str
    process_started: bool
    active_candidates: int
    furthest_stage_order: int
    furthest_interview_round: int


def _normalize(v: Any, default: str) -> str:
    if not isinstance(v, str):
        return default
    return v.strip().lower() or default


def get_policy_context(requisition: JobRequisition) -> PolicyContext:
    metadata = requisition.metadata or {}
    policy = metadata.get('hiring_policy') if isinstance(metadata, dict) else {}
    policy = policy if isinstance(policy, dict) else {}

    mode = _normalize(policy.get('mode'), 'on_the_go')
    strictness = _normalize(policy.get('strictness'), 'non_strict')

    apps_qs = Application.objects.filter(
        tenant_id=requisition.tenant_id,
        requisition_id=requisition.id,
        is_deleted=False,
    )
    active_candidates = apps_qs.count()
    process_started = active_candidates > 0

    stage_ids = list(apps_qs.values_list('current_stage_id', flat=True))
    furthest_stage_order = 0
    if stage_ids:
        furthest_stage_order = (
            JobStage.objects.filter(requisition_id=requisition.id, id__in=stage_ids, is_active=True)
            .order_by('-stage_order')
            .values_list('stage_order', flat=True)
            .first()
            or 0
        )

    furthest_interview_round = (
        Interview.objects.filter(
            tenant_id=requisition.tenant_id,
            requisition_id=requisition.id,
            is_deleted=False,
        )
        .order_by('-interview_round')
        .values_list('interview_round', flat=True)
        .first()
        or 0
    )

    return PolicyContext(
        mode=mode,
        strictness=strictness,
        process_started=process_started,
        active_candidates=active_candidates,
        furthest_stage_order=furthest_stage_order,
        furthest_interview_round=furthest_interview_round,
    )


def validate_workflow_toggle(requisition: JobRequisition, incoming: dict[str, Any]) -> str | None:
    ctx = get_policy_context(requisition)
    if not ctx.process_started:
        return None

    tracked = ('workflow_enabled', 'workflow_template_id', 'is_workflow_controlled')
    changed = any(k in incoming and incoming.get(k) != getattr(requisition, k) for k in tracked)
    if not changed:
        return None

    if ctx.mode == 'on_the_go':
        return 'Workflow automation cannot be changed after process start in On-the-Go mode.'
    if ctx.mode == 'predefined' and ctx.strictness == 'strict':
        return 'Predefined Strict policy locks workflow settings after process start.'

    # Non-strict predefined: allow disabling only, block enabling/retargeting.
    if incoming.get('workflow_enabled') is True and requisition.workflow_enabled is not True:
        return 'Workflow automation can only be enabled before process start.'
    if 'workflow_template_id' in incoming and incoming.get('workflow_template_id') != requisition.workflow_template_id:
        return 'Workflow template cannot be changed after process start.'
    return None


def validate_stage_create(requisition: JobRequisition, stage_order: int) -> str | None:
    ctx = get_policy_context(requisition)
    if not ctx.process_started:
        return None
    if ctx.mode == 'predefined' and ctx.strictness == 'strict':
        return 'Predefined Strict policy locks pipeline edits after process start.'
    if stage_order <= ctx.furthest_stage_order:
        return f'Only stages after current progress can be added. Furthest reached stage order is {ctx.furthest_stage_order}.'
    return None


def validate_stage_update(requisition: JobRequisition, stage: JobStage, incoming: dict[str, Any]) -> str | None:
    ctx = get_policy_context(requisition)
    if not ctx.process_started:
        return None
    if ctx.mode == 'predefined' and ctx.strictness == 'strict':
        return 'Predefined Strict policy locks pipeline edits after process start.'

    guarded_fields = {'name', 'stage_order', 'stage_type', 'stage_zone', 'trigger_type', 'trigger_config', 'responsible_role', 'decision_authority'}
    changed_guarded = any(field in incoming and incoming.get(field) != getattr(stage, field) for field in guarded_fields)
    if not changed_guarded:
        return None
    if stage.stage_order <= ctx.furthest_stage_order:
        return f"Stage '{stage.name}' is already in or behind active progress and cannot be structurally changed."
    return None


def validate_stage_delete(requisition: JobRequisition, stage: JobStage) -> str | None:
    ctx = get_policy_context(requisition)
    if not ctx.process_started:
        return None
    return f"Stage '{stage.name}' cannot be deleted after process start."


def validate_stage_reorder(requisition: JobRequisition) -> str | None:
    ctx = get_policy_context(requisition)
    if not ctx.process_started:
        return None
    return 'Stage reordering is disabled after process start. Add new stages at the end only.'


def _round_signature(round_obj: Any) -> tuple:
    if not isinstance(round_obj, dict):
        return ('', '', '', 0)
    return (
        str(round_obj.get('name', '')),
        str(round_obj.get('type', '')),
        str(round_obj.get('template_id', '')),
        int(round_obj.get('threshold_score') or 0),
    )


def validate_interview_rounds_change(requisition: JobRequisition, existing_rounds: list[Any], incoming_rounds: list[Any] | None) -> str | None:
    ctx = get_policy_context(requisition)
    if not ctx.process_started:
        return None
    if ctx.mode == 'predefined' and ctx.strictness == 'strict':
        return 'Predefined Strict policy locks interview flow changes after process start.'

    if not isinstance(incoming_rounds, list) or len(incoming_rounds) == 0:
        return 'Interview flow changes after process start must be append-only with explicit rounds_override.'

    r = ctx.furthest_interview_round
    if r <= 0:
        return None
    if len(incoming_rounds) < r or len(existing_rounds) < r:
        return f'Cannot shorten interview flow after progress. Furthest reached interview round is {r}.'

    for i in range(r):
        if _round_signature(existing_rounds[i]) != _round_signature(incoming_rounds[i]):
            return f'Interview rounds 1-{r} are already in progress and cannot be modified. Add new rounds after round {r}.'
    return None
