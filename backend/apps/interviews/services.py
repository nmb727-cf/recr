"""
Interview Service Layer
=======================
Encapsulates all business logic for the Interview Command Center.
Views delegate mutations here; views only handle HTTP concerns.

All methods are keyword-only (`*`) to prevent positional argument mistakes.
"""
from django.utils import timezone
from django.db.models import Avg
from collections import Counter

from apps.core import events
from apps.interviews.models import (
    Interview,
    InterviewType,
    InterviewTemplate,
    InterviewPanelist,
    InterviewFeedback,
    InterviewDecision,
    InterviewDecisionHistory,
    InterviewQuestion,
)


class InterviewTypeService:

    @staticmethod
    def list_registry(*, active_only: bool = False):
        qs = InterviewType.objects.filter(is_deleted=False).order_by('name')
        if active_only:
            qs = qs.filter(is_active=True)
        return qs

    @staticmethod
    def get(*, code: str):
        return InterviewType.objects.filter(code=code, is_deleted=False).first()

    @staticmethod
    def create(*, name: str, code: str, description: str = '',
               execution_mode: str = 'native',
               configurable: bool = True,
               type_configuration: dict | None = None) -> InterviewType:
        return InterviewType.objects.create(
            name=name,
            code=code,
            description=description,
            execution_mode=execution_mode,
            configurable=configurable,
            type_configuration=type_configuration or {},
        )


class InterviewTemplateService:

    @staticmethod
    def list_for_tenant(*, tenant_id) -> 'QuerySet':
        return InterviewTemplate.objects.filter(
            tenant_id=tenant_id,
            is_active=True,
            is_deleted=False,
        )

    @staticmethod
    def create(*, tenant_id, created_by, name: str, interview_type: str,
               duration_minutes: int = 30, instructions: str = '',
               scoring_type: str = 'numeric', type_id=None, **kwargs) -> InterviewTemplate:
        return InterviewTemplate.objects.create(
            tenant_id=tenant_id,
            created_by=created_by,
            name=name,
            interview_type=interview_type,
            type_id=type_id,
            duration_minutes=duration_minutes,
            instructions=instructions,
            scoring_type=scoring_type,
            **kwargs,
        )

    @staticmethod
    def soft_delete(*, template: InterviewTemplate, actor_id=None):
        template.soft_delete()


class InterviewService:

    @staticmethod
    def create(*, tenant_id, candidate_id, application_id, requisition_id,
               created_by, interview_type: str, scheduled_at=None,
               template_id=None, title: str = '', interview_round: int = 1,
               meeting_link: str = '', metadata: dict = None) -> Interview:
        """
        Schedule a new interview.  Copies questions from template when provided.
        Fires: events.interview.scheduled
        """
        interview = Interview.objects.create(
            tenant_id=tenant_id,
            candidate_id=candidate_id,
            application_id=application_id,
            requisition_id=requisition_id,
            created_by=created_by,
            interview_type=interview_type,
            scheduled_at=scheduled_at,
            template_id=template_id,
            title=title,
            interview_round=interview_round,
            interview_link=meeting_link,
            status='scheduled',
            metadata=metadata or {},
        )

        # Seed questions from template when available
        if template_id:
            try:
                template = InterviewTemplate.objects.get(
                    id=template_id,
                    tenant_id=tenant_id,
                    is_deleted=False,
                )
                InterviewService._seed_questions_from_template(
                    interview=interview,
                    template=template,
                    tenant_id=tenant_id,
                )
            except InterviewTemplate.DoesNotExist:
                pass

        events.interview.scheduled.send(
            sender=InterviewService,
            interview=interview,
        )
        return interview

    @staticmethod
    def _seed_questions_from_template(*, interview: Interview,
                                      template: InterviewTemplate,
                                      tenant_id) -> None:
        for i, q in enumerate(template.questions):
            InterviewQuestion.objects.create(
                tenant_id=tenant_id,
                interview_id=interview.id,
                question_text=q.get('text', ''),
                question_type=q.get('type', 'text'),
                options=q.get('options', []),
                expected_duration_seconds=q.get('duration'),
                order_index=i,
            )

    @staticmethod
    def start(*, interview: Interview) -> Interview:
        """
        Transition to in_progress.
        Fires: events.interview.started
        """
        if interview.status != 'scheduled':
            raise ValueError(f"Cannot start interview in status '{interview.status}'.")

        interview.status = 'in_progress'
        interview.started_at = timezone.now()
        interview.save(update_fields=['status', 'started_at', 'updated_at'])

        events.interview.started.send(sender=InterviewService, interview=interview)
        return interview

    @staticmethod
    def complete(*, interview: Interview, overall_score=None,
                 recommendation: str = '', feedback_summary: str = '') -> Interview:
        """
        Transition to completed, calculate aggregate human_score from feedback records.
        Fires: events.interview.completed + events.application.interviewed
        """
        if interview.status != 'in_progress':
            raise ValueError(f"Cannot complete interview in status '{interview.status}'.")

        # Aggregate human score from structured feedback
        agg = InterviewFeedback.objects.filter(
            interview_id=interview.id,
            is_deleted=False,
            score__isnull=False,
        ).aggregate(avg=Avg('score'))
        computed_human_score = agg['avg']

        interview.status = 'completed'
        interview.completed_at = timezone.now()
        interview.overall_score = overall_score
        interview.human_score = computed_human_score
        interview.recommendation = recommendation
        interview.feedback_summary = feedback_summary
        interview.save(update_fields=[
            'status', 'completed_at', 'overall_score', 'human_score',
            'recommendation', 'feedback_summary', 'updated_at',
        ])

        events.interview.completed.send(sender=InterviewService, interview=interview)

        # Notify application pipeline
        try:
            from apps.pipeline.models import Application
            application = Application.objects.get(id=interview.application_id)
            events.application.interviewed.send(
                sender=InterviewService,
                application=application,
                interview=interview,
            )
        except Exception:
            pass

        return interview

    @staticmethod
    def cancel(*, interview: Interview, reason: str = '') -> Interview:
        """
        Cancel a non-terminal interview.
        Fires: events.interview.cancelled
        """
        if interview.status in ('completed', 'cancelled'):
            raise ValueError(
                f"Cannot cancel an interview that is already '{interview.status}'."
            )

        interview.status = 'cancelled'
        if reason:
            interview.feedback_summary = f"Cancelled: {reason}"
        interview.save(update_fields=['status', 'feedback_summary', 'updated_at'])

        events.interview.cancelled.send(sender=InterviewService, interview=interview)
        return interview

    @staticmethod
    def reschedule(*, interview: Interview, scheduled_at) -> Interview:
        """Reschedule and reset to scheduled status."""
        interview.scheduled_at = scheduled_at
        interview.status = 'rescheduled'
        interview.save(update_fields=['scheduled_at', 'status', 'updated_at'])
        return interview

    @staticmethod
    def add_panelist(*, tenant_id, interview: Interview, user_id,
                     role: str = 'panelist', deadline_at=None) -> InterviewPanelist:
        panelist, _ = InterviewPanelist.objects.get_or_create(
            interview_id=interview.id,
            interviewer_id=user_id,
            defaults={
                'tenant_id': tenant_id,
                'role': role,
                'deadline_at': deadline_at,
            },
        )
        return panelist


class InterviewFeedbackService:

    @staticmethod
    def submit(*, tenant_id, interview_id, panelist_id,
               score=None, notes: str = '', recommendation: str = '',
               criteria_scores: dict = None, scorecard_ratings: dict = None) -> InterviewFeedback:
        """
        Upsert structured feedback from a panelist.
        Updates Interview.human_score aggregate after submission.
        """
        feedback, _ = InterviewFeedback.objects.update_or_create(
            interview_id=interview_id,
            panelist_id=panelist_id,
            defaults={
                'tenant_id': tenant_id,
                'score': score,
                'notes': notes,
                'recommendation': recommendation,
                'criteria_scores': criteria_scores or {},
                'scorecard_ratings': scorecard_ratings or {},
                'is_deleted': False,
                'deleted_at': None,
            },
        )

        # Recalculate aggregate human score on the interview
        agg = InterviewFeedback.objects.filter(
            interview_id=interview_id,
            is_deleted=False,
            score__isnull=False,
        ).aggregate(avg=Avg('score'))
        if agg['avg'] is not None:
            Interview.objects.filter(id=interview_id).update(human_score=agg['avg'])

        return feedback

    @staticmethod
    def list_for_interview(*, interview_id, tenant_id):
        return InterviewFeedback.objects.filter(
            interview_id=interview_id,
            tenant_id=tenant_id,
            is_deleted=False,
        )


class InterviewDecisionService:

    ROLE_WEIGHTS = {
        'lead': 2.0,
        'panelist': 1.0,
        'observer': 0.5,
        'note_taker': 0.5,
    }

    @staticmethod
    def record(*, tenant_id, interview: Interview, decision: str,
               notes: str = '', decided_by,
               decision_source: str = 'manual',
               decision_mode: str = 'manual',
               is_override: bool = False,
               override_reason: str = '',
               metadata: dict | None = None) -> InterviewDecision:
        """
        Upsert the final hiring decision for an interview.
        Fires: events.interview.decision_recorded
        """
        existing = InterviewDecision.objects.filter(interview_id=interview.id).first()
        previous_decision = existing.decision if existing else ''
        obj, created = InterviewDecision.objects.update_or_create(
            interview_id=interview.id,
            defaults={
                'tenant_id': tenant_id,
                'decision': decision,
                'decision_source': decision_source,
                'decision_mode': decision_mode,
                'notes': notes,
                'previous_decision': previous_decision,
                'is_override': is_override,
                'overridden_by': decided_by if is_override else None,
                'override_reason': override_reason,
                'decided_by': decided_by,
                'metadata': metadata or {},
            },
        )

        InterviewDecisionHistory.objects.create(
            tenant_id=tenant_id,
            interview_id=interview.id,
            decision_id=obj.id,
            previous_decision=previous_decision,
            new_decision=decision,
            changed_by=decided_by,
            change_source=decision_source,
            is_override=is_override,
            override_reason=override_reason,
            metadata=metadata or {},
        )

        events.interview.decision_recorded.send(
            sender=InterviewDecisionService,
            interview=interview,
            decision=obj,
            created=created,
        )
        return obj

    @staticmethod
    def get_for_interview(*, interview_id):
        return InterviewDecision.objects.filter(interview_id=interview_id).first()

    @staticmethod
    def history_for_interview(*, interview_id, tenant_id):
        return InterviewDecisionHistory.objects.filter(
            interview_id=interview_id,
            tenant_id=tenant_id,
        ).order_by('-changed_at')

    @staticmethod
    def multi_interviewer_recommendation(*, interview: Interview):
        feedback_qs = InterviewFeedback.objects.filter(
            interview_id=interview.id,
            is_deleted=False,
        )
        panel_map = {
            str(p.interviewer_id): p
            for p in InterviewPanelist.objects.filter(interview_id=interview.id)
        }
        majority_counter = Counter()
        weighted_counter = {}
        for fb in feedback_qs:
            rec = (fb.recommendation or '').strip()
            if not rec:
                continue
            majority_counter[rec] += 1
            role = (panel_map.get(str(fb.panelist_id)).role if panel_map.get(str(fb.panelist_id)) else 'panelist')
            weighted_counter[rec] = weighted_counter.get(rec, 0.0) + float(
                InterviewDecisionService.ROLE_WEIGHTS.get(role, 1.0)
            )

        majority = majority_counter.most_common(1)[0][0] if majority_counter else None
        weighted = None
        if weighted_counter:
            weighted = sorted(weighted_counter.items(), key=lambda x: (-x[1], x[0]))[0][0]
        return {
            'majority_vote': majority,
            'weighted_decision': weighted or majority,
            'majority_counts': dict(majority_counter),
            'weighted_scores': weighted_counter,
        }

    @staticmethod
    def evaluate(*, interview: Interview, source_inputs: dict | None = None, thresholds: dict | None = None):
        payload = source_inputs or {}
        cfg = thresholds or {}
        upper = float(cfg.get('next_round_min', 80))
        lower = float(cfg.get('reject_max', 50))

        score = payload.get('score')
        if score is None:
            score = interview.human_score if interview.human_score is not None else interview.overall_score
        try:
            numeric_score = float(score) if score is not None else None
        except Exception:
            numeric_score = None

        panel = InterviewDecisionService.multi_interviewer_recommendation(interview=interview)
        if payload.get('hiring_manager_override'):
            return {
                'decision': payload.get('hiring_manager_override'),
                'decision_source': 'manual',
                'decision_mode': 'manual',
                'rationale': 'hiring manager override',
                'panel': panel,
            }
        if numeric_score is not None and numeric_score > upper:
            return {
                'decision': 'next_round',
                'decision_source': 'automation_rules',
                'decision_mode': 'conditional',
                'rationale': f'score {numeric_score} > {upper}',
                'panel': panel,
            }
        if numeric_score is not None and numeric_score < lower:
            return {
                'decision': 'reject',
                'decision_source': 'automation_rules',
                'decision_mode': 'conditional',
                'rationale': f'score {numeric_score} < {lower}',
                'panel': panel,
            }

        recommended = panel.get('weighted_decision') or panel.get('majority_vote')
        if recommended:
            return {
                'decision': recommended,
                'decision_source': 'interviewer_feedback',
                'decision_mode': 'auto',
                'rationale': 'derived from panel feedback aggregation',
                'panel': panel,
            }
        return {
            'decision': 'manual_review',
            'decision_source': 'manual',
            'decision_mode': 'manual',
            'rationale': 'insufficient signals; manual review required',
            'panel': panel,
        }
