from datetime import timedelta
from typing import Optional, Tuple

from django.db.models import Q
from django.utils import timezone
from django.db.utils import ProgrammingError, OperationalError

from apps.agencies.models import AgencyClientRelationship
from apps.candidates.models import Candidate, CandidateRightsAuditLog, CandidateTenantRight
from apps.core import events


PROTECTED_BLOCKED_ACTIONS = {
    'add_to_reusable_database',
    'create_company_association',
    'reuse_for_another_job',
    'manual_import_candidate',
    'export_candidate',
    'share_candidate_externally',
    'detach_agency_relationship',
}

PROTECTED_ALLOWED_ACTIONS = {
    'view_candidate',
    'review_candidate',
    'workflow_allowed_job',
    'schedule_interview',
    'submit_feedback',
    'reject_candidate',
    'hire_via_agency_flow',
}


def _now():
    return timezone.now()


def _log_right_action(
    *,
    right: Optional[CandidateTenantRight],
    candidate_id,
    tenant_id=None,
    action: str,
    actor_user_id=None,
    actor_tenant_id=None,
    reason: str = '',
    metadata: Optional[dict] = None,
):
    CandidateRightsAuditLog.objects.create(
        tenant_right=right,
        candidate_id=candidate_id,
        tenant_id=tenant_id,
        action=action,
        actor_user_id=actor_user_id,
        actor_tenant_id=actor_tenant_id,
        reason=reason or '',
        metadata=metadata or {},
    )


def get_retention_config_for_relationship(*, agency_tenant_id, company_tenant_id):
    rel = AgencyClientRelationship.objects.filter(
        agency_tenant_id=agency_tenant_id,
        company_tenant_id=company_tenant_id,
        is_deleted=False,
    ).order_by('-updated_at').first()
    if not rel:
        return None
    return {
        'relationship_id': rel.id,
        'retention_enabled': bool(rel.retention_enabled),
        'retention_days': int(rel.retention_days or 0),
        'retention_start_type': rel.retention_start_type or 'submission_date',
        'retention_scope': rel.retention_scope or 'job_only',
        'retention_post_expiry': rel.retention_post_expiry or 'shared',
    }


def _calculate_protected_until(
    *,
    start_type: str,
    retention_days: int,
    now_dt,
):
    if retention_days <= 0:
        return now_dt
    if start_type == 'submission_date':
        return now_dt + timedelta(days=retention_days)
    if start_type == 'last_activity_date':
        return now_dt + timedelta(days=retention_days)
    return None


def create_or_update_protection_on_submission(
    *,
    candidate_id,
    source_tenant_id,
    target_tenant_id,
    context_job_id=None,
    actor_user_id=None,
):
    config = get_retention_config_for_relationship(
        agency_tenant_id=source_tenant_id,
        company_tenant_id=target_tenant_id,
    )
    if not config or not config['retention_enabled']:
        return None

    now_dt = _now()
    protected_until = _calculate_protected_until(
        start_type=config['retention_start_type'],
        retention_days=config['retention_days'],
        now_dt=now_dt,
    )
    pending_rejection_start = config['retention_start_type'] == 'rejection_date'

    right = CandidateTenantRight.objects.filter(
        candidate_id=candidate_id,
        source_tenant_id=source_tenant_id,
        target_tenant_id=target_tenant_id,
        is_deleted=False,
    ).filter(
        Q(status__in=['active', 'active_shared']) | Q(relationship_type='protected')
    ).order_by('-updated_at').first()

    allowed_job_ids = []
    if right and right.allowed_job_ids:
        allowed_job_ids = list(dict.fromkeys(right.allowed_job_ids))
    if context_job_id:
        job_id_str = str(context_job_id)
        if job_id_str not in allowed_job_ids:
            allowed_job_ids.append(job_id_str)

    base_metadata = dict(right.metadata) if right else {}
    base_metadata.update({
        'retention_relationship_id': str(config['relationship_id']),
        'retention_days': config['retention_days'],
        'retention_start_type': config['retention_start_type'],
        'retention_scope': config['retention_scope'],
        'retention_post_expiry': config['retention_post_expiry'],
        'pending_rejection_start': pending_rejection_start,
        'protection_started_at': now_dt.isoformat(),
    })

    if right:
        right.relationship_type = 'protected'
        right.status = 'active'
        right.protected_until = protected_until
        right.context_job_id = context_job_id or right.context_job_id
        right.allowed_job_ids = allowed_job_ids
        right.retention_scope = config['retention_scope']
        right.retention_start_type = config['retention_start_type']
        right.retention_post_expiry = config['retention_post_expiry']
        right.metadata = base_metadata
        right.save(update_fields=[
            'relationship_type', 'status', 'protected_until', 'context_job_id',
            'allowed_job_ids', 'retention_scope', 'retention_start_type',
            'retention_post_expiry', 'metadata', 'updated_at',
        ])
    else:
        right = CandidateTenantRight.objects.create(
            tenant_id=target_tenant_id,
            candidate_id=candidate_id,
            source_tenant_id=source_tenant_id,
            target_tenant_id=target_tenant_id,
            relationship_type='protected',
            protected_until=protected_until,
            context_job_id=context_job_id,
            allowed_job_ids=allowed_job_ids,
            retention_scope=config['retention_scope'],
            retention_start_type=config['retention_start_type'],
            retention_post_expiry=config['retention_post_expiry'],
            placed_via_source=False,
            status='active',
            created_by=actor_user_id,
            metadata=base_metadata,
        )

    _log_right_action(
        right=right,
        candidate_id=candidate_id,
        tenant_id=target_tenant_id,
        action='protection_created',
        actor_user_id=actor_user_id,
        actor_tenant_id=source_tenant_id,
        metadata={
            'context_job_id': str(context_job_id) if context_job_id else None,
            'protected_until': right.protected_until.isoformat() if right.protected_until else None,
            'retention_scope': right.retention_scope,
        },
    )

    events.candidate.protection_started.send(
        sender=CandidateTenantRight,
        right=right,
        candidate_id=candidate_id,
        source_tenant_id=source_tenant_id,
        target_tenant_id=target_tenant_id,
    )
    return right


def get_active_protection(*, candidate_id, target_tenant_id):
    now_dt = _now()
    try:
        right = CandidateTenantRight.objects.filter(
            candidate_id=candidate_id,
            target_tenant_id=target_tenant_id,
            relationship_type='protected',
            status='active',
            is_deleted=False,
        ).filter(
            Q(protected_until__isnull=True) | Q(protected_until__gt=now_dt)
        ).order_by('-updated_at').first()
        return right
    except (ProgrammingError, OperationalError):
        # Migration race-safe fallback: never crash candidate APIs if rights table
        # is not yet present in DB.
        return None


def protection_badge_payload(*, candidate_id, target_tenant_id):
    right = get_active_protection(candidate_id=candidate_id, target_tenant_id=target_tenant_id)
    if not right:
        return {
            'is_agency_protected': False,
            'protection_scope': None,
            'protected_until': None,
            'protection_status': None,
        }
    return {
        'is_agency_protected': True,
        'protection_scope': right.retention_scope,
        'protected_until': right.protected_until,
        'protection_status': right.status,
    }


def check_protected_action(
    *,
    candidate_id,
    tenant_id,
    action: str,
    job_id=None,
    actor_user_id=None,
) -> Tuple[bool, Optional[str], Optional[CandidateTenantRight]]:
    right = get_active_protection(candidate_id=candidate_id, target_tenant_id=tenant_id)
    if not right:
        return True, None, None

    # During protection, only explicit allowed actions are available.
    if action in PROTECTED_BLOCKED_ACTIONS:
        until_txt = right.protected_until.date().isoformat() if right.protected_until else 'agreement release'
        message = f"Candidate is protected under agency agreement until {until_txt}"
        _log_right_action(
            right=right,
            candidate_id=candidate_id,
            tenant_id=tenant_id,
            action='protected_action_blocked',
            actor_user_id=actor_user_id,
            actor_tenant_id=tenant_id,
            reason=message,
            metadata={'blocked_action': action, 'job_id': str(job_id) if job_id else None},
        )
        events.candidate.protected_action_blocked.send(
            sender=CandidateTenantRight,
            right=right,
            action=action,
            tenant_id=tenant_id,
            candidate_id=candidate_id,
        )
        return False, message, right

    if action not in PROTECTED_ALLOWED_ACTIONS:
        until_txt = right.protected_until.date().isoformat() if right.protected_until else 'agreement release'
        return False, f"Candidate is protected under agency agreement until {until_txt}", right

    # job_only scope means actions can only happen on linked jobs.
    if right.retention_scope == 'job_only':
        linked_jobs = set(right.allowed_job_ids or [])
        if right.context_job_id:
            linked_jobs.add(str(right.context_job_id))
        if job_id and str(job_id) not in linked_jobs:
            message = "Candidate is protected under agency agreement for job-scoped usage only."
            _log_right_action(
                right=right,
                candidate_id=candidate_id,
                tenant_id=tenant_id,
                action='protected_action_blocked',
                actor_user_id=actor_user_id,
                actor_tenant_id=tenant_id,
                reason=message,
                metadata={'blocked_action': action, 'job_id': str(job_id)},
            )
            return False, message, right
        if action != 'view_candidate' and not job_id:
            message = "Candidate is protected under agency agreement for a specific job context."
            return False, message, right

    if right.retention_scope in ['view_only', 'limited_company_access']:
        disallowed = {'add_to_reusable_database', 'reuse_for_another_job', 'create_company_association'}
        if action in disallowed:
            until_txt = right.protected_until.date().isoformat() if right.protected_until else 'agreement release'
            return False, f"Candidate is protected under agency agreement until {until_txt}", right

    if right.retention_start_type == 'last_activity_date':
        retention_days = int((right.metadata or {}).get('retention_days') or 0)
        right.protected_until = _now() + timedelta(days=max(retention_days, 0))
        metadata = dict(right.metadata or {})
        metadata['last_activity_at'] = _now().isoformat()
        right.metadata = metadata
        right.save(update_fields=['protected_until', 'metadata', 'updated_at'])

    return True, None, right


def find_duplicate_protected_candidate(
    *,
    tenant_id,
    email='',
    phone='',
    passport_id=None,
    global_hash='',
):
    filters = Q()
    if email:
        filters |= Q(email__iexact=email.strip().lower())
    if phone:
        phone_val = phone.strip()
        filters |= Q(phone=phone_val) | Q(phone_number=phone_val)
    if passport_id:
        filters |= Q(passport_id=passport_id)
    if global_hash:
        filters |= Q(global_hash=global_hash)
    if not filters:
        return None, None

    candidate = Candidate.objects.filter(is_deleted=False).filter(filters).order_by('-updated_at').first()
    if not candidate:
        return None, None
    right = get_active_protection(candidate_id=candidate.id, target_tenant_id=tenant_id)
    return candidate, right


def mark_direct_apply_during_protection(*, candidate_id, tenant_id, actor_user_id=None):
    right = get_active_protection(candidate_id=candidate_id, target_tenant_id=tenant_id)
    if not right:
        return None
    metadata = dict(right.metadata or {})
    metadata['direct_apply_during_protection'] = True
    metadata['direct_apply_flagged_at'] = _now().isoformat()
    right.metadata = metadata
    right.save(update_fields=['metadata', 'updated_at'])
    _log_right_action(
        right=right,
        candidate_id=candidate_id,
        tenant_id=tenant_id,
        action='direct_apply_conflict_flagged',
        actor_user_id=actor_user_id,
        actor_tenant_id=tenant_id,
    )
    return right


def start_rejection_based_protection_if_needed(*, candidate_id, tenant_id, actor_user_id=None):
    right = CandidateTenantRight.objects.filter(
        candidate_id=candidate_id,
        target_tenant_id=tenant_id,
        relationship_type='protected',
        retention_start_type='rejection_date',
        status='active',
        is_deleted=False,
    ).order_by('-updated_at').first()
    if not right:
        return None
    if right.protected_until:
        return right

    retention_days = int((right.metadata or {}).get('retention_days') or 0)
    right.protected_until = _now() + timedelta(days=max(retention_days, 0))
    metadata = dict(right.metadata or {})
    metadata['pending_rejection_start'] = False
    metadata['rejection_started_at'] = _now().isoformat()
    right.metadata = metadata
    right.save(update_fields=['protected_until', 'metadata', 'updated_at'])
    _log_right_action(
        right=right,
        candidate_id=candidate_id,
        tenant_id=tenant_id,
        action='protection_rejection_clock_started',
        actor_user_id=actor_user_id,
        actor_tenant_id=tenant_id,
    )
    return right


def mark_placement_via_source(*, candidate_id, tenant_id, actor_user_id=None):
    right = CandidateTenantRight.objects.filter(
        candidate_id=candidate_id,
        target_tenant_id=tenant_id,
        relationship_type='protected',
        status='active',
        is_deleted=False,
    ).order_by('-updated_at').first()
    if not right:
        return None

    right.placed_via_source = True
    if right.retention_post_expiry == 'shared':
        right.relationship_type = 'shared'
        right.status = 'active_shared'
        right.save(update_fields=['placed_via_source', 'relationship_type', 'status', 'updated_at'])
    else:
        right.save(update_fields=['placed_via_source', 'updated_at'])
    _log_right_action(
        right=right,
        candidate_id=candidate_id,
        tenant_id=tenant_id,
        action='placement_marked_via_source',
        actor_user_id=actor_user_id,
        actor_tenant_id=tenant_id,
    )
    events.candidate.rights_changed.send(
        sender=CandidateTenantRight,
        right=right,
        candidate_id=right.candidate_id,
        target_tenant_id=right.target_tenant_id,
        relationship_type=right.relationship_type,
        status=right.status,
    )
    return right


def expire_protection_rights(*, now_dt=None):
    now_dt = now_dt or _now()
    try:
        due = CandidateTenantRight.objects.filter(
            relationship_type='protected',
            status='active',
            is_deleted=False,
            protected_until__isnull=False,
            protected_until__lte=now_dt,
        )
    except (ProgrammingError, OperationalError):
        return 0
    updated = 0
    for right in due:
        if right.retention_post_expiry == 'shared':
            right.relationship_type = 'shared'
            right.status = 'active_shared'
        elif right.retention_post_expiry == 'company_use':
            right.status = 'released'
        else:
            right.status = 'pending_candidate_consent'

        right.save(update_fields=['relationship_type', 'status', 'updated_at'])
        _log_right_action(
            right=right,
            candidate_id=right.candidate_id,
            tenant_id=right.target_tenant_id,
            action='protection_expired',
            actor_tenant_id=right.target_tenant_id,
            metadata={'post_expiry': right.retention_post_expiry},
        )
        events.candidate.protection_expired.send(
            sender=CandidateTenantRight,
            right=right,
            candidate_id=right.candidate_id,
            target_tenant_id=right.target_tenant_id,
        )
        events.candidate.rights_changed.send(
            sender=CandidateTenantRight,
            right=right,
            candidate_id=right.candidate_id,
            target_tenant_id=right.target_tenant_id,
            relationship_type=right.relationship_type,
            status=right.status,
        )
        updated += 1
    return updated
