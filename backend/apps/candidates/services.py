import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q
from datetime import timedelta

from apps.candidates.models import Candidate, CandidateEngagement, CandidateTimelineEvent
from shared.owner_contracts import OwnerActionContext, OwnerActionResult, OwnerContractError


class CandidateAssignmentService:
    EXTERNAL_SOURCE_ORCHESTRATION_CENTER = 'orchestration_center'

    @staticmethod
    def assign_candidate_owner(
        *,
        tenant_id,
        candidate_id,
        owner_user_id,
        assigned_by=None,
        assignment_reason: str = '',
        sync_active_engagement: bool = True,
        metadata: dict | None = None,
        external_source: str = EXTERNAL_SOURCE_ORCHESTRATION_CENTER,
        external_reference: str = '',
    ):
        parsed_candidate_id = CandidateAssignmentService._parse_uuid(candidate_id)
        parsed_owner_user_id = CandidateAssignmentService._parse_uuid(owner_user_id)
        if not parsed_candidate_id:
            raise ValueError('Candidate assignment requires a valid UUID candidate_id.')
        if not parsed_owner_user_id:
            raise ValueError('Candidate assignment requires a valid UUID owner_user_id.')

        candidate = Candidate.objects.filter(
            tenant_id=tenant_id,
            id=parsed_candidate_id,
            is_deleted=False,
        ).first()
        if not candidate:
            raise ValueError('Candidate not found for assignment.')
        owner = get_user_model().objects.filter(
            id=parsed_owner_user_id,
            tenant_id=tenant_id,
            is_deleted=False,
        ).first()
        if not owner:
            raise ValueError('Candidate assignment requires an existing owner user in the same tenant.')

        engagement = None
        if sync_active_engagement:
            engagement = CandidateEngagement.objects.filter(
                tenant_id=tenant_id,
                candidate_id=parsed_candidate_id,
                is_active=True,
                is_deleted=False,
            ).order_by('-created_at').first()

        no_candidate_change = candidate.owner_user_id == parsed_owner_user_id
        no_engagement_change = not engagement or engagement.owner_user_id == parsed_owner_user_id
        if no_candidate_change and no_engagement_change:
            return candidate, engagement, False

        candidate.owner_user_id = parsed_owner_user_id
        candidate.save(update_fields=['owner_user_id', 'updated_at'])

        if engagement and engagement.owner_user_id != parsed_owner_user_id:
            engagement.owner_user_id = parsed_owner_user_id
            engagement.save(update_fields=['owner_user_id', 'updated_at'])

        CandidateTimelineEvent.objects.create(
            tenant_id=tenant_id,
            candidate_id=candidate.id,
            engagement=engagement,
            event_type='candidate.assigned',
            source='system',
            payload={
                'owner_user_id': str(parsed_owner_user_id),
                'assigned_by': str(assigned_by) if assigned_by else '',
                'assignment_reason': assignment_reason or 'automation_rule',
                'external_source': external_source,
                'external_reference': external_reference,
                **(metadata or {}),
            },
        )
        return candidate, engagement, True

    @staticmethod
    def _parse_uuid(value):
        if not value:
            return None
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError, AttributeError):
            return None

    @staticmethod
    def assign_from_orchestration(
        *,
        context: OwnerActionContext,
        candidate_id,
        owner_user_id,
        sync_active_engagement: bool = True,
        assignment_reason: str = 'automation_rule',
    ):
        try:
            candidate, engagement, created = CandidateAssignmentService.assign_candidate_owner(
                tenant_id=context.tenant_id,
                candidate_id=candidate_id,
                owner_user_id=owner_user_id,
                assigned_by=context.actor_id,
                assignment_reason=assignment_reason,
                sync_active_engagement=sync_active_engagement,
                metadata=context.audit_metadata,
                external_source=context.external_source,
                external_reference=context.external_reference,
            )
        except ValueError as exc:
            message = str(exc)
            if 'valid UUID' in message:
                raise OwnerContractError.validation(message) from exc
            if 'owner user in the same tenant' in message:
                raise OwnerContractError.ownership(message) from exc
            if 'Candidate not found' in message:
                raise OwnerContractError.not_found(message) from exc
            raise OwnerContractError.validation(message) from exc
        return OwnerActionResult(
            owner_module='candidates',
            action_family='assign',
            status='completed',
            target_type='candidate',
            target_id=str(candidate.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(assignment_reason=assignment_reason),
            payload={
                'candidate_id': str(candidate.id),
                'owner_user_id': str(candidate.owner_user_id) if candidate.owner_user_id else '',
                'engagement_id': str(engagement.id) if engagement else '',
            },
        )


class CandidateOperationalFlagService:
    EXTERNAL_SOURCE_ORCHESTRATION_CENTER = 'orchestration_center'
    ALLOWED_FLAGS = {'attention_needed', 'review_required', 'manual_check_required', 'overdue_risk'}

    @staticmethod
    def mark_operational_flag(
        *,
        tenant_id,
        entity_type: str,
        entity_id,
        flag_key: str,
        flag_value=True,
        metadata: dict | None = None,
        external_source: str = EXTERNAL_SOURCE_ORCHESTRATION_CENTER,
        external_reference: str = '',
        sync_active_engagement: bool = True,
    ):
        if flag_key not in CandidateOperationalFlagService.ALLOWED_FLAGS:
            raise ValueError('Unsupported candidate operational flag.')

        parsed_candidate_id = CandidateAssignmentService._parse_uuid(entity_id)
        if not parsed_candidate_id:
            raise ValueError('Candidate flagging requires a valid UUID entity_id.')
        if entity_type != 'candidate':
            raise ValueError('Unsupported candidate entity_type for flagging.')

        candidate = Candidate.objects.filter(
            tenant_id=tenant_id,
            id=parsed_candidate_id,
            is_deleted=False,
        ).first()
        if not candidate:
            raise ValueError('Candidate not found for flagging.')

        engagement = None
        if sync_active_engagement:
            engagement = CandidateEngagement.objects.filter(
                tenant_id=tenant_id,
                candidate_id=parsed_candidate_id,
                is_active=True,
                is_deleted=False,
            ).order_by('-created_at').first()

        payload = dict(metadata or {})
        payload['external_source'] = external_source
        if external_reference:
            payload['external_reference'] = external_reference
        comparable = {
            'value': bool(flag_value),
            **payload,
        }
        now_iso = timezone.now().isoformat()

        candidate_changed = CandidateOperationalFlagService._apply_flag(
            instance=candidate,
            comparable=comparable,
            flag_key=flag_key,
            now_iso=now_iso,
        )
        engagement_changed = False
        if engagement:
            engagement_changed = CandidateOperationalFlagService._apply_flag(
                instance=engagement,
                comparable=comparable,
                flag_key=flag_key,
                now_iso=now_iso,
            )

        if not candidate_changed and not engagement_changed:
            return candidate, engagement, False

        CandidateTimelineEvent.objects.create(
            tenant_id=tenant_id,
            candidate=candidate,
            engagement=engagement,
            event_type='candidate.flagged',
            source='system',
            payload={
                'flag_key': flag_key,
                'flag_value': bool(flag_value),
                **payload,
            },
        )
        return candidate, engagement, True

    @staticmethod
    def _apply_flag(*, instance, comparable: dict, flag_key: str, now_iso: str) -> bool:
        metadata_json = dict(instance.metadata or {})
        flags = dict(metadata_json.get('operational_flags') or {})
        existing = flags.get(flag_key)
        if existing and {k: v for k, v in existing.items() if k != 'updated_at'} == comparable:
            return False

        flags[flag_key] = {
            **comparable,
            'updated_at': now_iso,
        }
        metadata_json['operational_flags'] = flags
        instance.metadata = metadata_json
        instance.save(update_fields=['metadata', 'updated_at'])
        return True

    @staticmethod
    def mark_flag_from_orchestration(
        *,
        context: OwnerActionContext,
        entity_type: str,
        entity_id,
        flag_key: str,
        flag_value=True,
        sync_active_engagement: bool = True,
    ):
        try:
            candidate, engagement, created = CandidateOperationalFlagService.mark_operational_flag(
                tenant_id=context.tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                flag_key=flag_key,
                flag_value=flag_value,
                metadata=context.audit_metadata,
                external_source=context.external_source,
                external_reference=context.external_reference,
                sync_active_engagement=sync_active_engagement,
            )
        except ValueError as exc:
            message = str(exc)
            if 'Unsupported candidate entity_type' in message or 'Unsupported candidate operational flag' in message:
                raise OwnerContractError.unsupported(message) from exc
            if 'valid UUID' in message:
                raise OwnerContractError.validation(message) from exc
            if 'Candidate not found' in message:
                raise OwnerContractError.not_found(message) from exc
            raise OwnerContractError.validation(message) from exc
        return OwnerActionResult(
            owner_module='candidates',
            action_family='mark_flag',
            status='completed',
            target_type='candidate',
            target_id=str(candidate.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(flag_key=flag_key, flag_value=bool(flag_value)),
            payload={
                'flag_key': flag_key,
                'candidate_id': str(candidate.id),
                'engagement_id': str(engagement.id) if engagement else '',
            },
        )


class CandidateIntelligenceService:
    @staticmethod
    def get_intelligence_profile(candidate: Candidate):
        """
        Generates candidate intelligence from the shared intelligence substrate.
        Keeps the response schema backward-compatible for existing UI consumers.
        """
        from apps.analytics.intelligence_substrate import IntelligenceAggregator

        snapshot = IntelligenceAggregator.build_candidate_intelligence(
            tenant_id=candidate.tenant_id,
            candidate_id=candidate.id,
        )
        signals = snapshot.get('signals', {})

        engagement = signals.get('engagement_signals', {})
        skill = signals.get('skill_match_signals', {})
        experience = signals.get('experience_signals', {})
        activity = signals.get('activity_signals', {})
        interview = signals.get('interview_signals', {})

        days_since_activity = engagement.get('days_since_last_activity', 999)
        availability_score = 100 if engagement.get('is_actively_looking') else 30
        engagement_score = max(0, 100 - min(int(days_since_activity), 120))

        availability_label = "Passive"
        if engagement.get('is_actively_looking'):
            availability_label = "Active"
        if days_since_activity <= 7:
            availability_label = "Engaged"
        elif days_since_activity >= 90:
            availability_label = "Stale"

        active_app_count = activity.get('active_application_count', 0)
        pipeline_label = "Idle"
        if active_app_count > 0:
            pipeline_label = "In Progress"
        if active_app_count > 0 and days_since_activity <= 3:
            pipeline_label = "Fast Moving"

        exp_years = float(experience.get('experience_years') or 0)
        seniority = "Junior"
        if exp_years > 10:
            seniority = "Principal / Lead"
        elif exp_years > 5:
            seniority = "Senior"
        elif exp_years > 2:
            seniority = "Mid-Level"

        fit_score = int(skill.get('fit_score') or 0)
        interview_score = int(interview.get('avg_interview_score') or 0)
        experience_score = min(100, int(exp_years * 8))
        readiness_score = int((availability_score * 0.4) + (engagement_score * 0.3) + (candidate.profile_completeness * 0.3))
        confidence_score = min(
            100,
            (
                25
                + (25 if candidate.skills else 0)
                + (25 if interview.get('completed_interviews', 0) > 0 else 0)
                + (25 if exp_years > 0 else 0)
            ),
        )

        rationale = []
        if fit_score >= 80:
            rationale.append("Strong skill match")
        if interview_score >= 70:
            rationale.append("Strong interview performance")
        if pipeline_label == "Fast Moving":
            rationale.append("High hiring velocity")
        if availability_label in ("Active", "Engaged"):
            rationale.append("Responsive and engaged")

        return {
            'scores': {
                'fit': fit_score,
                'readiness': readiness_score,
                'potential': int((experience_score * 0.3) + (interview_score * 0.7)) if interview_score else int(experience_score),
                'confidence': confidence_score
            },
            'labels': {
                'availability': availability_label,
                'seniority': seniority,
                'pipeline': pipeline_label,
                'category': CandidateIntelligenceService._categorize(fit_score, readiness_score, pipeline_label)
            },
            'factors': {
                'experience_strength': int(experience_score),
                'skill_relevance': fit_score,
                'engagement_level': int(engagement_score),
                'interview_performance': int(interview_score)
            },
            'explainable_ai': {
                'rationale': rationale,
                'summary': f"Scored {fit_score}% fit based on {', '.join(rationale) if rationale else 'profile alignment'}."
            },
            'substrate_snapshot_at': snapshot.get('computed_at'),
        }

    @staticmethod
    def _categorize(fit, readiness, pipeline):
        if fit > 85 and readiness > 70: return "Best Fit"
        if fit > 70 and pipeline == "Fast Moving": return "Fast Hire"
        if fit < 60 and readiness > 80: return "High Potential"
        return "Fallback"

    @staticmethod
    def calculate_job_fit(candidate: Candidate, job_id: uuid.UUID):
        """
        Robust Job Fit Engine (CIL v2).
        Uses skill depth, must-have matching, and experience thresholds.
        """
        from apps.jobs.models import JobRequisition
        job = JobRequisition.objects.filter(id=job_id).first()
        if not job:
            return 0
        
        # 1. Skill Depth Match (60%)
        candidate_skills = set(s.lower() for s in (candidate.skills or []))
        job_skills = set(s.lower() for s in (job.skills_required or []))
        
        if not job_skills:
            skill_score = 50
        else:
            overlap = candidate_skills.intersection(job_skills)
            skill_score = (len(overlap) / len(job_skills)) * 100
        
        # 2. Role Relevance & Seniority (20%)
        role_score = 100
        if candidate.experience_years and job.experience_min:
            if candidate.experience_years < job.experience_min:
                role_score = 50 # Partial match
            elif candidate.experience_years > (job.experience_max or 100):
                role_score = 80 # Overqualified
        
        # 3. Knowledge Evidence (20%)
        # Assessment/Interview alignment would go here
        evidence_score = 50 # Baseline
        
        total_score = (skill_score * 0.6) + (role_score * 0.2) + (evidence_score * 0.2)
        return int(min(100, total_score))
