from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.core.cache import cache
from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.core import events


ACTIVE_APPLICATION_STATUSES = ('applied', 'sourcing', 'screening', 'shortlisted', 'interview', 'assessment', 'offer')


@dataclass
class IntelligenceSnapshot:
    tenant_id: Any
    entity_type: str
    entity_id: str
    payload: dict


class IntelligenceCache:
    """Tenant-safe snapshot cache with namespace-based invalidation."""

    DEFAULT_TTL_SECONDS = 300

    @staticmethod
    def _ns_key(tenant_id, kind: str) -> str:
        return f"intel:ns:{tenant_id}:{kind}"

    @classmethod
    def _ns_value(cls, tenant_id, kind: str) -> int:
        key = cls._ns_key(tenant_id, kind)
        value = cache.get(key)
        if value is None:
            value = 1
            cache.set(key, value, timeout=86400)
        return int(value)

    @classmethod
    def make_key(cls, *, tenant_id, kind: str, entity_id: str) -> str:
        ns = cls._ns_value(tenant_id, kind)
        return f"intel:snapshot:{tenant_id}:{kind}:v{ns}:{entity_id}"

    @classmethod
    def get(cls, *, tenant_id, kind: str, entity_id: str):
        return cache.get(cls.make_key(tenant_id=tenant_id, kind=kind, entity_id=entity_id))

    @classmethod
    def set(
        cls,
        *,
        tenant_id,
        kind: str,
        entity_id: str,
        payload: dict,
        ttl_seconds: int | None = None,
    ) -> None:
        cache.set(
            cls.make_key(tenant_id=tenant_id, kind=kind, entity_id=entity_id),
            payload,
            timeout=ttl_seconds or cls.DEFAULT_TTL_SECONDS,
        )

    @classmethod
    def invalidate_kind(cls, *, tenant_id, kind: str) -> int:
        key = cls._ns_key(tenant_id, kind)
        current = cache.get(key) or 1
        nxt = int(current) + 1
        cache.set(key, nxt, timeout=86400)
        return nxt

    @classmethod
    def invalidate_many(cls, *, tenant_id, kinds: list[str]) -> None:
        for kind in kinds:
            cls.invalidate_kind(tenant_id=tenant_id, kind=kind)


class IntelligenceSignals:
    """Independent signal builders used by all intelligence projections."""

    @staticmethod
    def job_signals(*, tenant_id, requisition_id) -> dict:
        from apps.jobs.models import JobRequisition, JobStage
        from apps.pipeline.models import ActionDeadline, Application, ApplicationStageHistory

        now = timezone.now()
        job = JobRequisition.objects.filter(id=requisition_id, tenant_id=tenant_id, is_deleted=False).first()
        if not job:
            return {}

        apps = Application.objects.filter(tenant_id=tenant_id, requisition_id=requisition_id, is_deleted=False)
        total_apps = apps.count()
        active_apps = apps.filter(status__in=ACTIVE_APPLICATION_STATUSES)
        active_count = active_apps.count()
        age_days = max(1, (now - job.created_at).days)

        stage_rows = active_apps.values('current_stage_id').annotate(count=Count('id'))
        stages = {
            row['id']: row['name']
            for row in JobStage.objects.filter(requisition_id=requisition_id, is_active=True).values('id', 'name')
        }
        bottlenecks = []
        for row in stage_rows:
            count = row['count']
            if active_count and (count / active_count) >= 0.4 and count >= 3:
                stage_id = row['current_stage_id']
                bottlenecks.append(
                    {
                        'stage_id': str(stage_id) if stage_id else None,
                        'stage_name': stages.get(stage_id, 'Unassigned Stage'),
                        'count': count,
                        'share': round((count / active_count) * 100, 1),
                    }
                )

        stage_moves_14d = ApplicationStageHistory.objects.filter(
            tenant_id=tenant_id,
            application_id__in=apps.values_list('id', flat=True),
            moved_at__gte=now - timedelta(days=14),
        ).count()

        overdue_actions = ActionDeadline.objects.filter(
            tenant_id=tenant_id,
            entity_type='application',
            entity_id__in=apps.values_list('id', flat=True),
            status='pending',
            deadline_at__lt=now,
        ).count()

        aging_candidates = active_apps.filter(updated_at__lt=now - timedelta(days=7)).count()
        approval_delays = 1 if job.status == 'draft' and age_days >= 3 else 0
        application_rate = round(total_apps / age_days, 2)

        return {
            'application_rate': application_rate,
            'pipeline_movement_14d': stage_moves_14d,
            'stage_bottlenecks': bottlenecks,
            'aging_candidates': aging_candidates,
            'sla_violations': overdue_actions,
            'approval_delays': approval_delays,
            'active_candidates': active_count,
            'total_candidates': total_apps,
            'job_age_days': age_days,
        }

    @staticmethod
    def candidate_signals(*, tenant_id, candidate_id) -> dict:
        from apps.candidates.models import Candidate
        from apps.interviews.models import Interview
        from apps.pipeline.models import Application

        candidate = Candidate.objects.filter(id=candidate_id, is_deleted=False).first()
        if not candidate:
            return {}

        now = timezone.now()
        apps = Application.objects.filter(candidate_id=candidate.id, is_deleted=False)
        interviews = Interview.objects.filter(candidate_id=candidate.id, is_deleted=False)

        engagement_days = None
        if candidate.last_activity_at:
            engagement_days = (now - candidate.last_activity_at).days

        avg_match = apps.aggregate(avg=Avg('match_score'))['avg']
        avg_interview = interviews.filter(status='completed').aggregate(avg=Avg('overall_score'))['avg']

        return {
            'engagement_signals': {
                'is_actively_looking': bool(candidate.is_actively_looking),
                'days_since_last_activity': engagement_days if engagement_days is not None else 999,
            },
            'skill_match_signals': {
                'fit_score': int(candidate.fit_score or 0),
                'avg_match_score': float(avg_match) if avg_match is not None else 0.0,
            },
            'experience_signals': {
                'experience_years': float(candidate.experience_years or 0),
                'current_title': candidate.current_title or '',
                'current_company': candidate.current_company or '',
            },
            'activity_signals': {
                'application_count': apps.count(),
                'active_application_count': apps.filter(status__in=ACTIVE_APPLICATION_STATUSES).count(),
            },
            'interview_signals': {
                'completed_interviews': interviews.filter(status='completed').count(),
                'avg_interview_score': float(avg_interview) if avg_interview is not None else 0.0,
            },
        }

    @staticmethod
    def pipeline_signals(*, tenant_id, requisition_id=None) -> dict:
        from apps.pipeline.models import Application

        now = timezone.now()
        apps = Application.objects.filter(tenant_id=tenant_id, is_deleted=False)
        if requisition_id:
            apps = apps.filter(requisition_id=requisition_id)

        total = apps.count()
        if total == 0:
            return {
                'stuck_stage': 0,
                'drop_rate': 0.0,
                'conversion_rate': 0.0,
                'recruiter_activity': 0,
                'status_breakdown': {},
            }

        stale = apps.filter(status__in=ACTIVE_APPLICATION_STATUSES, updated_at__lt=now - timedelta(days=7)).count()
        dropped = apps.filter(status__in=('rejected', 'withdrawn')).count()
        converted = apps.filter(status='joined').count()
        recruiter_activity = apps.filter(updated_at__gte=now - timedelta(days=3)).count()
        status_breakdown = {
            row['status']: row['count'] for row in apps.values('status').annotate(count=Count('id'))
        }

        return {
            'stuck_stage': stale,
            'drop_rate': round((dropped / total) * 100, 2),
            'conversion_rate': round((converted / total) * 100, 2),
            'recruiter_activity': recruiter_activity,
            'status_breakdown': status_breakdown,
        }

    @staticmethod
    def system_signals(*, tenant_id) -> dict:
        from apps.accounts.models import CustomUser
        from apps.jobs.models import JobRequisition
        from apps.pipeline.models import Application

        now = timezone.now()
        recruiter_ids = list(
            CustomUser.objects.filter(
                tenant_id=tenant_id,
                role__in=('tenant_admin', 'hr_manager', 'recruiter'),
                is_active=True,
                is_deleted=False,
            ).values_list('id', flat=True)
        )
        recruiter_count = len(recruiter_ids)
        active_jobs = JobRequisition.objects.filter(
            tenant_id=tenant_id, status='active', is_deleted=False
        ).count()
        monthly_hires = Application.objects.filter(
            tenant_id=tenant_id,
            status='joined',
            joined_at__gte=now - timedelta(days=30),
            is_deleted=False,
        ).count()
        recruiter_load = round((active_jobs / recruiter_count), 2) if recruiter_count else 0.0

        return {
            'recruiter_load': recruiter_load,
            'hiring_velocity_30d': monthly_hires,
            'active_jobs': active_jobs,
            'recruiter_count': recruiter_count,
        }


class IntelligenceAggregator:
    """Canonical substrate entrypoint for intelligence snapshots."""

    @staticmethod
    def _build_insights_from_job_signals(signals: dict) -> list[dict]:
        insights: list[dict] = []
        if signals.get('aging_candidates', 0) > 0:
            insights.append(
                {
                    'type': 'aging_candidates',
                    'severity': 'medium',
                    'message': f"{signals['aging_candidates']} active candidates are aging in pipeline.",
                }
            )
        if signals.get('sla_violations', 0) > 0:
            insights.append(
                {
                    'type': 'sla_violations',
                    'severity': 'high',
                    'message': f"{signals['sla_violations']} overdue action deadlines detected.",
                }
            )
        if signals.get('stage_bottlenecks'):
            top = signals['stage_bottlenecks'][0]
            insights.append(
                {
                    'type': 'stage_bottleneck',
                    'severity': 'high',
                    'message': f"{top['stage_name']} has {top['count']} candidates ({top['share']}%).",
                }
            )
        return insights

    @classmethod
    def build_job_intelligence(cls, *, tenant_id, requisition_id, force_refresh: bool = False) -> dict:
        cache_kind = 'job'
        entity_id = str(requisition_id)
        if not force_refresh:
            cached = IntelligenceCache.get(tenant_id=tenant_id, kind=cache_kind, entity_id=entity_id)
            if cached:
                return cached

        from apps.jobs.intelligence_engine import JobIntelligenceEngine

        engine_data = JobIntelligenceEngine.get_job_intelligence(tenant_id, requisition_id)
        signals = IntelligenceSignals.job_signals(tenant_id=tenant_id, requisition_id=requisition_id)
        payload = {
            'entity': 'job',
            'entity_id': entity_id,
            'engine': engine_data,
            'signals': signals,
            'insights': cls._build_insights_from_job_signals(signals),
            'computed_at': timezone.now().isoformat(),
        }
        IntelligenceCache.set(tenant_id=tenant_id, kind=cache_kind, entity_id=entity_id, payload=payload)
        return payload

    @classmethod
    def build_candidate_intelligence(cls, *, tenant_id, candidate_id, force_refresh: bool = False) -> dict:
        cache_kind = 'candidate'
        entity_id = str(candidate_id)
        if not force_refresh:
            cached = IntelligenceCache.get(tenant_id=tenant_id, kind=cache_kind, entity_id=entity_id)
            if cached:
                return cached

        signals = IntelligenceSignals.candidate_signals(tenant_id=tenant_id, candidate_id=candidate_id)
        payload = {
            'entity': 'candidate',
            'entity_id': entity_id,
            'signals': signals,
            'computed_at': timezone.now().isoformat(),
        }
        IntelligenceCache.set(tenant_id=tenant_id, kind=cache_kind, entity_id=entity_id, payload=payload)
        return payload

    @classmethod
    def build_pipeline_intelligence(cls, *, tenant_id, requisition_id=None, force_refresh: bool = False) -> dict:
        cache_kind = 'pipeline'
        entity_id = str(requisition_id) if requisition_id else 'global'
        if not force_refresh:
            cached = IntelligenceCache.get(tenant_id=tenant_id, kind=cache_kind, entity_id=entity_id)
            if cached:
                return cached

        signals = IntelligenceSignals.pipeline_signals(tenant_id=tenant_id, requisition_id=requisition_id)
        payload = {
            'entity': 'pipeline',
            'entity_id': entity_id,
            'signals': signals,
            'computed_at': timezone.now().isoformat(),
        }
        IntelligenceCache.set(tenant_id=tenant_id, kind=cache_kind, entity_id=entity_id, payload=payload)
        return payload

    @classmethod
    def build_recruiter_intelligence(cls, *, tenant_id, recruiter_id=None, force_refresh: bool = False) -> dict:
        from apps.jobs.models import JobRequisition
        from apps.pipeline.models import Application

        cache_kind = 'recruiter'
        entity_id = str(recruiter_id) if recruiter_id else 'global'
        if not force_refresh:
            cached = IntelligenceCache.get(tenant_id=tenant_id, kind=cache_kind, entity_id=entity_id)
            if cached:
                return cached

        jobs = JobRequisition.objects.filter(tenant_id=tenant_id, is_deleted=False)
        apps = Application.objects.filter(tenant_id=tenant_id, is_deleted=False)
        if recruiter_id:
            jobs = jobs.filter(recruiter_id=recruiter_id)
            apps = apps.filter(created_by=recruiter_id)

        payload = {
            'entity': 'recruiter',
            'entity_id': entity_id,
            'signals': {
                'assigned_jobs': jobs.count(),
                'active_jobs': jobs.filter(status='active').count(),
                'active_pipeline': apps.filter(status__in=ACTIVE_APPLICATION_STATUSES).count(),
                'offers': apps.filter(status='offer').count(),
                'joins': apps.filter(status='joined').count(),
            },
            'computed_at': timezone.now().isoformat(),
        }
        IntelligenceCache.set(tenant_id=tenant_id, kind=cache_kind, entity_id=entity_id, payload=payload)
        return payload

    @classmethod
    def build_global_intelligence(cls, *, tenant_id, force_refresh: bool = False) -> dict:
        cache_kind = 'global'
        entity_id = 'global'
        if not force_refresh:
            cached = IntelligenceCache.get(tenant_id=tenant_id, kind=cache_kind, entity_id=entity_id)
            if cached:
                return cached

        system = IntelligenceSignals.system_signals(tenant_id=tenant_id)
        pipeline = cls.build_pipeline_intelligence(tenant_id=tenant_id, requisition_id=None, force_refresh=force_refresh)
        payload = {
            'entity': 'global',
            'entity_id': 'global',
            'signals': {
                'system': system,
                'pipeline': pipeline.get('signals', {}),
            },
            'computed_at': timezone.now().isoformat(),
        }
        IntelligenceCache.set(tenant_id=tenant_id, kind=cache_kind, entity_id=entity_id, payload=payload)
        return payload


class IntelligenceEventTriggers:
    """Invalidates and emits intelligence updates when domain events occur."""

    @staticmethod
    def _emit_snapshot_event(*, tenant_id, event_name: str, entity_type: str | None = None, entity_id: str | None = None):
        try:
            signal = getattr(events, 'intelligence', None)
            if signal and getattr(signal, 'snapshot_updated', None):
                signal.snapshot_updated.send(
                    sender=IntelligenceEventTriggers.__class__,
                    tenant_id=tenant_id,
                    event_name=event_name,
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
        except Exception:
            return

    @classmethod
    def handle_domain_event(
        cls,
        *,
        event_name: str,
        tenant_id,
        requisition_id=None,
        candidate_id=None,
        recruiter_id=None,
    ) -> None:
        if not tenant_id:
            return

        invalidate_kinds = {'global', 'pipeline'}
        if requisition_id:
            invalidate_kinds.add('job')
        if candidate_id:
            invalidate_kinds.add('candidate')
        if recruiter_id:
            invalidate_kinds.add('recruiter')

        IntelligenceCache.invalidate_many(tenant_id=tenant_id, kinds=sorted(invalidate_kinds))
        cls._emit_snapshot_event(
            tenant_id=tenant_id,
            event_name=event_name,
            entity_type='job' if requisition_id else ('candidate' if candidate_id else None),
            entity_id=str(requisition_id or candidate_id) if (requisition_id or candidate_id) else None,
        )
