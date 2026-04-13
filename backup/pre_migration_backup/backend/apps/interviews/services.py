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
    InterviewReviewTask,
    InterviewQuestion,
    INTERVIEW_TYPE_REGISTRY_DEFAULTS,
)
from shared.owner_contracts import OwnerActionContext, OwnerActionResult, OwnerContractError


class InterviewTypeService:

    @staticmethod
    def list_registry(*, active_only: bool = False):
        for row in INTERVIEW_TYPE_REGISTRY_DEFAULTS:
            InterviewType.objects.update_or_create(
                code=row['code'],
                defaults={
                    'name': row['name'],
                    'description': row.get('description', ''),
                    'execution_mode': row.get('execution_mode', 'native'),
                    'configurable': True,
                    'is_active': True,
                },
            )
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
    def trigger_next_round(*, tenant_id, application_id, job_id, candidate_id, current_round: int = 0):
        """
        Starts the next interview round for an application based on Job's InterviewPackageBinding.
        """
        from apps.interviews.models import InterviewPackageBinding, Interview, InterviewTemplate, InterviewScorecardTemplate, InterviewQuestion
        
        binding = InterviewPackageBinding.objects.filter(
            tenant_id=tenant_id,
            job_id=job_id,
            is_deleted=False
        ).first()
        
        if not binding:
            return None, "No interview package bound to this job."
            
        next_round_num = current_round + 1
        round_config = binding.get_round_config(next_round_num)
        
        if not round_config:
            return None, f"No configuration found for round {next_round_num}."
            
        # Create Interview
        interview_type = round_config.get('type')
        if isinstance(interview_type, dict):
            interview_type = interview_type.get('code')
            
        template_id = round_config.get('template_id')
        scorecard_template_id = None
        
        if interview_type:
            default_scorecard = InterviewScorecardTemplate.objects.filter(
                tenant_id=tenant_id,
                interview_type=interview_type,
                is_active=True,
                is_deleted=False,
            ).order_by('-updated_at').first()
            if default_scorecard:
                scorecard_template_id = default_scorecard.id

        interview = Interview.objects.create(
            tenant_id=tenant_id,
            application_id=application_id,
            candidate_id=candidate_id,
            requisition_id=job_id,
            interview_type=interview_type or 'ai_screening',
            interview_round=next_round_num,
            title=round_config.get('name', f"Round {next_round_num}"),
            status='scheduled',
            template_id=template_id,
            scorecard_template_id=scorecard_template_id,
            execution_mode='native', # Default to native
        )
        
        # If template provided, copy questions
        if template_id:
            try:
                template = InterviewTemplate.objects.get(id=template_id, is_deleted=False)
                questions_to_create = []
                for i, q in enumerate(template.questions):
                    questions_to_create.append(InterviewQuestion(
                        tenant_id=tenant_id,
                        interview_id=interview.id,
                        question_text=q.get('text', ''),
                        question_type=q.get('type', 'text'),
                        options=q.get('options', []),
                        expected_duration_seconds=q.get('duration', None),
                        order_index=i,
                    ))
                if questions_to_create:
                    InterviewQuestion.objects.bulk_create(questions_to_create)
            except InterviewTemplate.DoesNotExist:
                pass
                
        return interview, "Interview scheduled."

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

    @staticmethod
    def get_job_interview_snapshot(*, tenant_id, job_id):
        """
        Returns aggregate interview stats for a specific job.
        Used by the Job Command Center.
        """
        from apps.interviews.models import Interview, InterviewPackageBinding
        from apps.pipeline.models import Application

        binding = InterviewPackageBinding.objects.filter(
            tenant_id=tenant_id,
            job_id=job_id,
            is_deleted=False
        ).first()

        interviews = Interview.objects.filter(
            tenant_id=tenant_id,
            requisition_id=job_id,
            is_deleted=False
        )

        candidates_in_interview = Application.objects.filter(
            tenant_id=tenant_id,
            requisition_id=job_id,
            status='interview',
            is_deleted=False
        ).count()

        pending_interviews = interviews.filter(status__in=['scheduled', 'rescheduled']).count()
        completed_interviews = interviews.filter(status='completed').count()
        cancelled_interviews = interviews.filter(status='cancelled').count()

        return {
            'binding_active': binding is not None,
            'package_name': binding.package.title if binding else None,
            'automation_enabled': binding.automation_enabled if binding else False,
            'candidates_in_interview': candidates_in_interview,
            'pending_interviews': pending_interviews,
            'completed_interviews': completed_interviews,
            'cancelled_interviews': cancelled_interviews,
            'rounds_summary': binding.get_rounds() if binding else [],
        }


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


class InterviewReviewTaskService:
    AUTOMATION_REVIEW_TYPES = {
        'ai_output_review',
        'interview_review',
        'interview_feedback_review',
        'manual_check_review',
    }

    @staticmethod
    def create_task(
        *,
        tenant_id,
        interview_id,
        review_type: str,
        requested_by=None,
        assigned_role: str = '',
        assigned_reviewer_id=None,
        due_at=None,
        notes: str = '',
        metadata: dict | None = None,
        external_reference: str = '',
    ):
        if external_reference:
            existing = InterviewReviewTask.objects.filter(
                tenant_id=tenant_id,
                interview_id=interview_id,
                review_type=review_type,
                status='pending',
                external_reference=external_reference,
            ).first()
            if existing:
                return existing, False
        task = InterviewReviewTask.objects.create(
            tenant_id=tenant_id,
            interview_id=interview_id,
            review_type=review_type,
            requested_by=requested_by,
            assigned_role=assigned_role,
            assigned_reviewer_id=assigned_reviewer_id,
            due_at=due_at,
            external_reference=external_reference,
            notes=notes,
            metadata=metadata or {},
        )
        return task, True

    @staticmethod
    def create_automation_review_task(
        *,
        tenant_id,
        owner_module: str,
        entity_type: str,
        entity_id,
        review_type: str,
        requested_by=None,
        assigned_role: str = '',
        assigned_reviewer_id=None,
        due_at=None,
        notes: str = '',
        metadata: dict | None = None,
        external_reference: str = '',
        approval_required: bool = False,
        approver_role: str = '',
    ):
        if review_type not in InterviewReviewTaskService.AUTOMATION_REVIEW_TYPES:
            raise ValueError('Unsupported automation review task type.')
        task_metadata = dict(metadata or {})
        task_metadata.setdefault('owner_module', owner_module)
        task_metadata.setdefault('entity_type', entity_type)
        task_metadata.setdefault('entity_id', str(entity_id))
        task_metadata.setdefault(
            'governance',
            {
                'approval_required': bool(approval_required),
                'approver_role': approver_role or 'tenant_admin',
            },
        )
        return InterviewReviewTaskService.create_task(
            tenant_id=tenant_id,
            interview_id=entity_id,
            review_type=review_type,
            requested_by=requested_by,
            assigned_role=assigned_role,
            assigned_reviewer_id=assigned_reviewer_id,
            due_at=due_at,
            notes=notes,
            metadata=task_metadata,
            external_reference=external_reference,
        )

    @staticmethod
    def create_from_orchestration(
        *,
        context: OwnerActionContext,
        owner_module: str,
        entity_type: str,
        entity_id,
        review_type: str,
        assigned_role: str = '',
        assigned_reviewer_id=None,
        due_at=None,
        notes: str = '',
        approval_required: bool = False,
        approver_role: str = '',
    ):
        try:
            task, created = InterviewReviewTaskService.create_automation_review_task(
                tenant_id=context.tenant_id,
                owner_module=owner_module,
                entity_type=entity_type,
                entity_id=entity_id,
                review_type=review_type,
                requested_by=context.actor_id,
                assigned_role=assigned_role,
                assigned_reviewer_id=assigned_reviewer_id,
                due_at=due_at,
                notes=notes,
                metadata=context.audit_metadata,
                external_reference=context.external_reference,
                approval_required=approval_required,
                approver_role=approver_role,
            )
        except ValueError as exc:
            message = str(exc)
            if 'Unsupported automation review task type' in message:
                raise OwnerContractError.unsupported(message) from exc
            raise OwnerContractError.validation(message) from exc
        return OwnerActionResult(
            owner_module='interviews',
            action_family='create_review_task',
            status='completed',
            target_type='review_task',
            target_id=str(task.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(
                owner_module=owner_module,
                entity_type=entity_type,
                review_type=review_type,
                approval_required=bool(approval_required),
                approver_role=approver_role or 'tenant_admin',
            ),
            payload={
                'review_task_id': str(task.id),
                'review_type': task.review_type,
                'assigned_role': task.assigned_role,
                'assigned_reviewer_id': str(task.assigned_reviewer_id) if task.assigned_reviewer_id else '',
                'owner_module': task.metadata.get('owner_module', owner_module),
                'entity_type': task.metadata.get('entity_type', entity_type),
                'entity_id': task.metadata.get('entity_id', str(entity_id)),
            },
        )

    @staticmethod
    def assign_task(
        *,
        tenant_id,
        interview_id,
        review_type: str,
        assigned_reviewer_id=None,
        assigned_role: str = '',
        external_reference: str = '',
    ):
        task = InterviewReviewTaskService._resolve_task(
            tenant_id=tenant_id,
            interview_id=interview_id,
            review_type=review_type,
            external_reference=external_reference,
        )
        if assigned_reviewer_id and str(task.assigned_reviewer_id or '') == str(assigned_reviewer_id) and task.assigned_role == assigned_role:
            return task, False
        task.assigned_reviewer_id = assigned_reviewer_id
        if assigned_role:
            task.assigned_role = assigned_role
        task.save(update_fields=['assigned_reviewer_id', 'assigned_role', 'updated_at'])
        return task, True

    @staticmethod
    def assign_from_orchestration(
        *,
        context: OwnerActionContext,
        interview_id,
        review_type: str,
        assigned_reviewer_id=None,
        assigned_role: str = '',
    ):
        try:
            task, created = InterviewReviewTaskService.assign_task(
                tenant_id=context.tenant_id,
                interview_id=interview_id,
                review_type=review_type,
                assigned_reviewer_id=assigned_reviewer_id,
                assigned_role=assigned_role,
                external_reference=context.external_reference,
            )
        except ValueError as exc:
            message = str(exc)
            if 'not found for assignment' in message:
                raise OwnerContractError.not_found(message) from exc
            raise OwnerContractError.validation(message) from exc
        return OwnerActionResult(
            owner_module='interviews',
            action_family='assign',
            status='completed',
            target_type='review_task',
            target_id=str(task.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(review_type=review_type),
            payload={
                'review_task_id': str(task.id),
                'assigned_reviewer_id': str(task.assigned_reviewer_id) if task.assigned_reviewer_id else '',
                'assigned_role': task.assigned_role,
            },
        )

    @staticmethod
    def mark_operational_flag(
        *,
        tenant_id,
        entity_type: str,
        entity_id,
        flag_key: str,
        flag_value=True,
        metadata: dict | None = None,
    ):
        allowed_flags = {'attention_needed', 'review_required', 'overdue_risk', 'manual_check_required'}
        if flag_key not in allowed_flags:
            raise ValueError('Unsupported interview operational flag.')
        payload = dict(metadata or {})
        now_iso = timezone.now().isoformat()
        if entity_type == 'interview':
            interview = Interview.objects.filter(tenant_id=tenant_id, id=entity_id, is_deleted=False).first()
            if not interview:
                raise ValueError('Interview not found for flagging.')
            metadata_json = dict(interview.metadata or {})
            flags = dict(metadata_json.get('operational_flags') or {})
            comparable = {'value': bool(flag_value), **payload}
            if flags.get(flag_key) and {k: v for k, v in flags[flag_key].items() if k != 'updated_at'} == comparable:
                return interview, False
            desired = {**comparable, 'updated_at': now_iso}
            flags[flag_key] = desired
            metadata_json['operational_flags'] = flags
            interview.metadata = metadata_json
            interview.save(update_fields=['metadata', 'updated_at'])
            return interview, True
        if entity_type == 'review_task':
            task = InterviewReviewTask.objects.filter(tenant_id=tenant_id, id=entity_id).first()
            if not task:
                raise ValueError('Interview review task not found for flagging.')
            metadata_json = dict(task.metadata or {})
            flags = dict(metadata_json.get('operational_flags') or {})
            comparable = {'value': bool(flag_value), **payload}
            if flags.get(flag_key) and {k: v for k, v in flags[flag_key].items() if k != 'updated_at'} == comparable:
                return task, False
            desired = {**comparable, 'updated_at': now_iso}
            flags[flag_key] = desired
            metadata_json['operational_flags'] = flags
            task.metadata = metadata_json
            task.save(update_fields=['metadata', 'updated_at'])
            return task, True
        raise ValueError('Unsupported interview entity_type for flagging.')

    @staticmethod
    def mark_flag_from_orchestration(
        *,
        context: OwnerActionContext,
        entity_type: str,
        entity_id,
        flag_key: str,
        flag_value=True,
    ):
        try:
            obj, created = InterviewReviewTaskService.mark_operational_flag(
                tenant_id=context.tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                flag_key=flag_key,
                flag_value=flag_value,
                metadata=context.audit_metadata,
            )
        except ValueError as exc:
            message = str(exc)
            if 'Unsupported interview entity_type' in message or 'Unsupported interview operational flag' in message:
                raise OwnerContractError.unsupported(message) from exc
            if 'not found for flagging' in message:
                raise OwnerContractError.not_found(message) from exc
            raise OwnerContractError.validation(message) from exc
        return OwnerActionResult(
            owner_module='interviews',
            action_family='mark_flag',
            status='completed',
            target_type=entity_type,
            target_id=str(obj.id),
            duplicate=not created,
            audit_metadata=context.metadata_payload(flag_key=flag_key, flag_value=bool(flag_value)),
            payload={
                'flag_key': flag_key,
                'entity_id': str(obj.id),
            },
        )

    @staticmethod
    def _resolve_task(*, tenant_id, interview_id, review_type: str, external_reference: str = ''):
        qs = InterviewReviewTask.objects.filter(
            tenant_id=tenant_id,
            interview_id=interview_id,
            review_type=review_type,
            status='pending',
        )
        if external_reference:
            qs = qs.filter(external_reference=external_reference)
        task = qs.order_by('-created_at').first()
        if not task:
            raise ValueError('Interview review task not found for assignment.')
        return task
