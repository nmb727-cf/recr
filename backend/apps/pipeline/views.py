import logging
from django.utils import timezone
from rest_framework import status

logger = logging.getLogger(__name__)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.pipeline.models import Application, ApplicationStageHistory, ActionDeadline
from apps.pipeline.serializers import (
    ApplicationSerializer,
    ApplicationStageHistorySerializer,
    ActionDeadlineSerializer,
)
from apps.core.responses import success_response, error_response
from shared.actor_access import is_candidate
from apps.candidates.protection import check_protected_action


def validate_application_move(application, target_stage=None, reason=None, user=None):
    """
    Centralized guard for manual application progression.

    Rules:
    - Internal automation (no user) is allowed.
    - Threshold automation actor is allowed.
    - Agency users cannot move stages.
    - Recruiters can move only when they own the requisition.
    """
    if user is None:
        return True, None

    actor_mode = str((getattr(user, 'metadata', {}) or {}).get('actor_mode', '')).strip().lower()
    if actor_mode == 'threshold_automation':
        return True, None

    user_role = str(getattr(user, 'role', '') or '').strip().lower()
    if user_role.startswith('agency_'):
        return False, "Agency users cannot move application stages."

    if user_role == 'recruiter':
        from apps.jobs.models import JobRequisition
        job = JobRequisition.objects.filter(id=application.requisition_id).first()
        if job and getattr(job, 'created_by', None) and str(job.created_by) != str(user.id):
            return False, "Only the requisition owner can move this application."

    return True, None

def perform_application_move(application, target_stage, user, notes=None, reason=None, request=None):
    """
    Performs the actual database updates, history recording, and event emission.
    """
    from apps.jobs.models import JobRequisition, JobStage
    from apps.pipeline.models import ApplicationStageHistory
    from django.utils import timezone
    from apps.core import events

    stage_note = (notes or reason or '').strip()
    if not stage_note:
        raise ValueError("A mandatory note/reason is required for every stage change.")

    current_stage = None
    if application.current_stage_id:
        try:
            current_stage = JobStage.objects.get(id=application.current_stage_id)
        except JobStage.DoesNotExist:
            pass

    old_stage_id = application.current_stage_id
    old_status = application.status

    # Update Application
    application.current_stage_id = target_stage.id
    application.status = target_stage.stage_type
    application_update_fields = ['current_stage_id', 'status', 'updated_at']
    if target_stage.stage_type == 'joined' and not application.joined_at:
        application.joined_at = timezone.now()
        application_update_fields.append('joined_at')
    application.save(update_fields=application_update_fields)

    # Record history
    ApplicationStageHistory.objects.create(
        tenant_id=user.tenant_id,
        application_id=application.id,
        from_stage_id=old_stage_id,
        to_stage_id=target_stage.id,
        from_status=old_status,
        to_status=target_stage.stage_type,
        moved_by=user.id,
        reason=stage_note,
        notes=stage_note,
        metadata={
            'previous_stage': old_status,
            'new_stage': target_stage.stage_type,
            'note': stage_note,
            'changed_by': str(user.id),
            'changed_at': timezone.now().isoformat(),
        },
    )

    # Hire Logic
    if target_stage.stage_type == 'joined':
        try:
            job = JobRequisition.objects.get(id=application.requisition_id)
            if job.headcount > 0:
                job.headcount -= 1
                job.save(update_fields=['headcount', 'updated_at'])
        except JobRequisition.DoesNotExist:
            pass

        # Commercial & Engagement Hooks
        from apps.pipeline.guarantee import on_candidate_hired, mark_placement_via_source
        try:
            on_candidate_hired(application, user)
        except Exception:
            pass
        mark_placement_via_source(
            candidate_id=application.candidate_id,
            tenant_id=application.tenant_id,
            actor_user_id=user.id,
        )

    # ─── Trigger Logic ────────────────────────────────────────────────────────
    
    # 1. Interview Trigger
    if target_stage.trigger_type == 'interview' or (not target_stage.trigger_type and target_stage.stage_type == 'interview'):
        from apps.interviews.services import InterviewService
        
        # If explicit trigger_config specifies a round, use it. Otherwise increment.
        round_to_trigger = target_stage.trigger_config.get('interview_round')
        if round_to_trigger is None:
            current_round = application.metadata.get('current_interview_round', 0)
            round_to_trigger = current_round + 1
            
        interview, message = InterviewService.trigger_next_round(
            tenant_id=user.tenant_id,
            application_id=application.id,
            job_id=application.requisition_id,
            candidate_id=application.candidate_id,
            current_round=round_to_trigger - 1 # trigger_next_round adds 1
        )
        if interview:
            application.metadata['current_interview_round'] = interview.interview_round
            application.save(update_fields=['metadata'])

    # 2. Prequalification Trigger
    if target_stage.trigger_type == 'prequal':
        from apps.jobs.prequal_service import evaluate_candidate_prequal
        try:
            eval_res = evaluate_candidate_prequal(
                job_id=str(application.requisition_id),
                candidate_id=str(application.candidate_id),
                tenant_id=str(user.tenant_id) if user.tenant_id else None
            )
            application.metadata['last_prequal_result'] = eval_res.get('result')
            application.metadata['last_prequal_score'] = eval_res.get('score')
            application.save(update_fields=['metadata'])
            
            # Auto-move based on prequal result if configured
            # (In a real system, we'd have a service handling the 'pass_action' / 'fail_action')
        except Exception as e:
            logger.error(f"Failed to trigger prequal for app {application.id}: {e}")

    # Event Emission
    events.application.stage_changed.send(
        sender=application.__class__,
        application=application,
        from_stage=current_stage,
        to_stage=target_stage,
        user=user,
        request=request
    )

    if target_stage.stage_type == 'interview':
        events.application.interviewed.send(sender=application.__class__, application=application, user=user, request=request)
    elif target_stage.stage_type == 'offer':
        events.application.offer_made.send(sender=application.__class__, application=application, user=user, request=request)
    elif target_stage.stage_type == 'joined':
        events.application.hired.send(sender=application.__class__, application=application, user=user, request=request)

    return application


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_application(pk, tenant_id):
    return Application.objects.filter(id=pk, tenant_id=tenant_id, is_deleted=False).first()


# ── Application views ─────────────────────────────────────────────────────────

class ApplicationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        qs = Application.objects.filter(tenant_id=request.user.tenant_id, is_deleted=False)
        requisition_id = request.query_params.get('requisition_id')
        candidate_id = request.query_params.get('candidate_id')
        app_status = request.query_params.get('status')
        stage_id = request.query_params.get('current_stage_id')
        if requisition_id:
            qs = qs.filter(requisition_id=requisition_id)
        if candidate_id:
            qs = qs.filter(candidate_id=candidate_id)
        if app_status:
            qs = qs.filter(status=app_status)
        if stage_id:
            qs = qs.filter(current_stage_id=stage_id)
        return success_response(data={
            'applications': ApplicationSerializer(qs.order_by('-created_at')[:500], many=True).data
        })

    def post(self, request):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        from apps.candidates.models import Candidate

        candidate_id = request.data.get('candidate_id')
        if not candidate_id:
            return error_response('candidate_id is required.')
        candidate_exists = Candidate.objects.filter(
            id=candidate_id,
            is_deleted=False,
        ).exists()
        if not candidate_exists:
            return error_response(
                'Candidate does not exist. Resolve candidate identity before creating application.',
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data['tenant_id'] = str(request.user.tenant_id) if request.user.tenant_id else None
        data['created_by'] = str(request.user.id) if request.user.id else None
        serializer = ApplicationSerializer(data=data)
        if not serializer.is_valid():
            return error_response('Validation failed.', serializer.errors)
        application = serializer.save()

        # ─── Workflow Master Trigger ───
        from apps.jobs.models import JobRequisition
        from apps.jobs.workflow_service import JobWorkflowService
        requisition = JobRequisition.objects.filter(id=application.requisition_id).first()
        if requisition:
            JobWorkflowService.trigger_job_workflow(
                requisition=requisition,
                event_type='application.created',
                context={
                    'application_id': str(application.id),
                    'candidate_id': str(application.candidate_id),
                }
            )

        return success_response(
            data={'application': ApplicationSerializer(application).data},
            status_code=status.HTTP_201_CREATED,
        )


class ApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        application = _get_application(pk, request.user.tenant_id)
        if not application:
            return error_response('Application not found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data={'application': ApplicationSerializer(application).data})

    def patch(self, request, pk):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        application = _get_application(pk, request.user.tenant_id)
        if not application:
            return error_response('Application not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = ApplicationSerializer(application, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response('Validation failed.', serializer.errors)
        serializer.save()
        return success_response(data={'application': serializer.data})

    def put(self, request, pk):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        application = _get_application(pk, request.user.tenant_id)
        if not application:
            return error_response('Application not found.', status_code=status.HTTP_404_NOT_FOUND)

        # Stage/status transitions through this endpoint are guarded and blocked.
        if any(k in request.data for k in ('status', 'current_stage_id', 'stage_id')):
            allowed, msg = validate_application_move(application, reason=request.data.get('note') or request.data.get('reason'), user=request.user)
            if not allowed:
                return error_response(msg or 'Stage transition is restricted.', status_code=status.HTTP_403_FORBIDDEN)

            protection_allowed, protection_msg, _ = check_protected_action(
                candidate_id=application.candidate_id,
                tenant_id=request.user.tenant_id,
                action='workflow_allowed_job',
                job_id=application.requisition_id,
                actor_user_id=request.user.id,
            )
            if not protection_allowed:
                return error_response(protection_msg, status_code=status.HTTP_403_FORBIDDEN)

            return error_response(
                'Use move-stage endpoint for status/stage changes.',
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = ApplicationSerializer(application, data=request.data, partial=False)
        if not serializer.is_valid():
            return error_response('Validation failed.', serializer.errors)
        serializer.save()
        return success_response(data={'application': serializer.data})


class ApplicationMoveStageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        from apps.jobs.models import JobStage
        application = _get_application(pk, request.user.tenant_id)
        if not application:
            return error_response('Application not found.', status_code=status.HTTP_404_NOT_FOUND)

        stage_id = request.data.get('stage_id')
        notes = request.data.get('notes') or request.data.get('note') or request.data.get('reason', '')
        if not stage_id:
            return error_response('stage_id is required.')

        target_stage = JobStage.objects.filter(
            id=stage_id, requisition_id=application.requisition_id
        ).first()
        if not target_stage:
            return error_response('Stage not found for this requisition.', status_code=status.HTTP_404_NOT_FOUND)

        ownership_allowed, ownership_msg = validate_application_move(
            application,
            target_stage,
            reason=notes,
            user=request.user,
        )
        if not ownership_allowed:
            return error_response(ownership_msg, status_code=status.HTTP_403_FORBIDDEN)

        protection_allowed, protection_msg, _ = check_protected_action(
            candidate_id=application.candidate_id,
            tenant_id=request.user.tenant_id,
            action='workflow_allowed_job',
            job_id=application.requisition_id,
            actor_user_id=request.user.id,
        )
        if not protection_allowed:
            return error_response(protection_msg, status_code=status.HTTP_403_FORBIDDEN)

        # ─── Workflow Master Control ───
        from apps.jobs.models import JobRequisition
        from apps.jobs.workflow_service import JobWorkflowService
        requisition = JobRequisition.objects.filter(id=application.requisition_id).first()
        if requisition:
            allowed, msg = JobWorkflowService.can_move_to_stage(requisition, application, target_stage, user=request.user)
            if not allowed:
                return error_response(msg or "Movement restricted by Workflow Master.")

        try:
            application = perform_application_move(
                application, target_stage, request.user, notes=notes, request=request
            )
        except ValueError as exc:
            return error_response(str(exc))

        return success_response(data={'application': ApplicationSerializer(application).data})


class ApplicationShortlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        application = _get_application(pk, request.user.tenant_id)
        if not application:
            return error_response('Application not found.', status_code=status.HTTP_404_NOT_FOUND)

        if application.status in ('rejected', 'withdrawn', 'joined'):
            return error_response(f'Cannot shortlist an application with status "{application.status}".')

        old_status = application.status
        # ─── Decision Authority Check ───
        from apps.jobs.models import JobRequisition, JobStage
        from apps.jobs.workflow_service import JobWorkflowService
        requisition = JobRequisition.objects.filter(id=application.requisition_id).first()
        shortlist_stage = None
        if requisition:
            # Prefer an explicit shortlisted stage when configured.
            shortlist_stage = (
                JobStage.objects.filter(requisition_id=requisition.id, stage_type='shortlisted')
                .order_by('stage_order')
                .first()
            )
            target_stage = shortlist_stage or JobStage.objects.filter(
                requisition_id=requisition.id,
                stage_type='screening',
            ).first()
            if target_stage:
                allowed, msg = JobWorkflowService.can_move_to_stage(
                    requisition,
                    application,
                    target_stage,
                    user=request.user,
                )
                if not allowed:
                    return error_response(msg or "Decision authority restricted.")
        notes = request.data.get('notes', 'Shortlisted')

        if shortlist_stage:
            try:
                application = perform_application_move(
                    application,
                    shortlist_stage,
                    request.user,
                    notes=notes,
                    request=request,
                )
            except ValueError as exc:
                return error_response(str(exc))
        else:
            # Backward compatibility for tenants without explicit shortlisted stage.
            application.status = 'shortlisted'
            application.save(update_fields=['status', 'updated_at'])

            ApplicationStageHistory.objects.create(
                tenant_id=request.user.tenant_id,
                application_id=application.id,
                from_stage_id=application.current_stage_id,
                to_stage_id=application.current_stage_id,
                from_status=old_status,
                to_status='shortlisted',
                moved_by=request.user.id,
                reason=notes,
                notes=notes,
            )

        return success_response(data={'application': ApplicationSerializer(application).data})


class ApplicationRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        application = _get_application(pk, request.user.tenant_id)
        if not application:
            return error_response('Application not found.', status_code=status.HTTP_404_NOT_FOUND)

        if application.status in ('rejected', 'withdrawn', 'joined'):
            return error_response(f'Application is already "{application.status}".')

        reason = request.data.get('reason', '').strip()
        category = request.data.get('category', '').strip()
        if not reason:
            return error_response('reason is required to reject an application.')

        old_status = application.status
        # ─── Decision Authority Check ───
        from apps.jobs.models import JobRequisition, JobStage
        from apps.jobs.workflow_service import JobWorkflowService
        requisition = JobRequisition.objects.filter(id=application.requisition_id).first()
        if requisition:
            # Rejection targets the 'rejected' stage type
            target_stage = JobStage.objects.filter(requisition_id=requisition.id, stage_type='rejected').first()
            if target_stage:
                allowed, msg = JobWorkflowService.can_move_to_stage(requisition, application, target_stage, user=request.user)
                if not allowed:
                    return error_response(msg or "Decision authority restricted.")

        application.status = 'rejected'
        application.rejection_reason = reason
        if category:
            application.rejection_category = category
        application.save(update_fields=['status', 'rejection_reason', 'rejection_category', 'updated_at'])

        ApplicationStageHistory.objects.create(
            tenant_id=request.user.tenant_id,
            application_id=application.id,
            from_stage_id=application.current_stage_id,
            to_stage_id=application.current_stage_id,
            from_status=old_status,
            to_status='rejected',
            moved_by=request.user.id,
            reason=reason,
            notes=reason,
        )

        return success_response(data={'application': ApplicationSerializer(application).data})


class ApplicationWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        application = _get_application(pk, request.user.tenant_id)
        if not application:
            return error_response('Application not found.', status_code=status.HTTP_404_NOT_FOUND)

        if application.status in ('rejected', 'withdrawn', 'joined'):
            return error_response(f'Application is already "{application.status}".')

        reason = request.data.get('reason', '').strip()
        if not reason:
            return error_response('reason is required to withdraw an application.')

        old_status = application.status
        application.status = 'withdrawn'
        application.withdrawn_reason = reason
        application.save(update_fields=['status', 'withdrawn_reason', 'updated_at'])

        ApplicationStageHistory.objects.create(
            tenant_id=request.user.tenant_id,
            application_id=application.id,
            from_stage_id=application.current_stage_id,
            to_stage_id=application.current_stage_id,
            from_status=old_status,
            to_status='withdrawn',
            moved_by=request.user.id,
            reason=reason,
            notes=reason,
        )

        return success_response(data={'application': ApplicationSerializer(application).data})


class ApplicationMakeOfferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        application = _get_application(pk, request.user.tenant_id)
        if not application:
            return error_response('Application not found.', status_code=status.HTTP_404_NOT_FOUND)

        if application.status in ('rejected', 'withdrawn', 'joined'):
            return error_response(f'Cannot make an offer for an application with status "{application.status}".')

        old_status = application.status
        # ─── Decision Authority Check ───
        from apps.jobs.models import JobRequisition, JobStage
        from apps.jobs.workflow_service import JobWorkflowService
        requisition = JobRequisition.objects.filter(id=application.requisition_id).first()
        if requisition:
            # Offer targets the 'offer' stage type
            target_stage = JobStage.objects.filter(requisition_id=requisition.id, stage_type='offer').first()
            if target_stage:
                allowed, msg = JobWorkflowService.can_move_to_stage(requisition, application, target_stage, user=request.user)
                if not allowed:
                    return error_response(msg or "Decision authority restricted.")

        update_fields = ['status', 'updated_at']

        application.status = 'offer'
        if request.data.get('offer_amount'):
            application.offer_amount = request.data['offer_amount']
            update_fields.append('offer_amount')
        if request.data.get('offer_currency'):
            application.offer_currency = request.data['offer_currency']
            update_fields.append('offer_currency')
        if request.data.get('offer_date'):
            application.offer_date = request.data['offer_date']
            update_fields.append('offer_date')
        if request.data.get('joining_date'):
            application.joining_date = request.data['joining_date']
            update_fields.append('joining_date')

        application.save(update_fields=update_fields)

        notes = request.data.get('notes', 'Offer made')
        ApplicationStageHistory.objects.create(
            tenant_id=request.user.tenant_id,
            application_id=application.id,
            from_stage_id=application.current_stage_id,
            to_stage_id=application.current_stage_id,
            from_status=old_status,
            to_status='offer',
            moved_by=request.user.id,
            reason=notes,
            notes=notes,
        )

        return success_response(data={'application': ApplicationSerializer(application).data})


# ── Pipeline view ─────────────────────────────────────────────────────────────

class PipelineView(APIView):
    """Kanban-style pipeline grouped by stage for a requisition."""
    permission_classes = [IsAuthenticated]

    def get(self, request, requisition_id):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        from apps.jobs.models import JobStage
        stages = JobStage.objects.filter(
            tenant_id=request.user.tenant_id,
            requisition_id=requisition_id,
        ).order_by('stage_order')

        applications = Application.objects.filter(
            tenant_id=request.user.tenant_id,
            requisition_id=requisition_id,
            is_deleted=False,
        ).exclude(status__in=['rejected', 'withdrawn'])

        app_by_stage = {}
        for app in applications:
            key = str(app.current_stage_id) if app.current_stage_id else 'unassigned'
            app_by_stage.setdefault(key, []).append(app)

        pipeline = []
        for stage in stages:
            stage_apps = app_by_stage.get(str(stage.id), [])
            pipeline.append({
                'stage': {
                    'id': str(stage.id),
                    'name': stage.name,
                    'stage_type': stage.stage_type,
                    'stage_order': stage.stage_order,
                    'action_deadline_hours': getattr(stage, 'action_deadline_hours', 48),
                },
                'count': len(stage_apps),
                'applications': ApplicationSerializer(stage_apps, many=True).data,
            })

        unassigned = app_by_stage.get('unassigned', [])
        if unassigned:
            pipeline.insert(0, {
                'stage': {
                    'id': None,
                    'name': 'Unassigned',
                    'stage_type': 'applied',
                    'stage_order': -1,
                    'action_deadline_hours': 48,
                },
                'count': len(unassigned),
                'applications': ApplicationSerializer(unassigned, many=True).data,
            })

        return success_response(data={'pipeline': pipeline, 'requisition_id': str(requisition_id)})


class RequisitionActivityView(APIView):
    """Stage history for all applications under a requisition."""
    permission_classes = [IsAuthenticated]

    def get(self, request, requisition_id):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        app_ids = Application.objects.filter(
            tenant_id=request.user.tenant_id,
            requisition_id=requisition_id,
            is_deleted=False,
        ).values_list('id', flat=True)

        history = ApplicationStageHistory.objects.filter(
            application_id__in=app_ids,
        ).order_by('-moved_at')[:200]

        return success_response(data={
            'activity': ApplicationStageHistorySerializer(history, many=True).data
        })


class BulkActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        action = request.data.get('action')
        application_ids = request.data.get('application_ids', [])
        notes = request.data.get('notes', '').strip()

        if not application_ids:
            return error_response('application_ids is required.')

        allowed_actions = ('shortlist', 'reject', 'withdraw')
        if action not in allowed_actions:
            return error_response(f'action must be one of: {", ".join(allowed_actions)}')

        if action in ('reject', 'withdraw') and not notes:
            return error_response(f'notes/reason is required for bulk {action}.')

        applications = Application.objects.filter(
            tenant_id=request.user.tenant_id,
            id__in=application_ids,
            is_deleted=False,
        ).exclude(status__in=['rejected', 'withdrawn', 'joined'])

        status_map = {'shortlist': 'shortlisted', 'reject': 'rejected', 'withdraw': 'withdrawn'}
        new_status = status_map[action]
        update_fields_map = {
            'reject': {'rejection_reason': notes},
            'withdraw': {'withdrawn_reason': notes},
        }

        updated_ids = []
        history_records = []
        for app in applications:
            old_status = app.status
            app.status = new_status
            if action == 'reject':
                app.rejection_reason = notes
            elif action == 'withdraw':
                app.withdrawn_reason = notes
            app.updated_at = timezone.now()
            updated_ids.append(app.id)
            history_records.append(ApplicationStageHistory(
                tenant_id=request.user.tenant_id,
                application_id=app.id,
                from_stage_id=app.current_stage_id,
                to_stage_id=app.current_stage_id,
                from_status=old_status,
                to_status=new_status,
                moved_by=request.user.id,
                reason=notes or action,
                notes=notes or action,
            ))

        save_fields = ['status', 'updated_at']
        if action == 'reject':
            save_fields.append('rejection_reason')
        elif action == 'withdraw':
            save_fields.append('withdrawn_reason')

        Application.objects.bulk_update(applications, save_fields)
        ApplicationStageHistory.objects.bulk_create(history_records)

        return success_response(data={'updated_count': len(updated_ids), 'updated_ids': [str(i) for i in updated_ids]})


# ── Deadline views ────────────────────────────────────────────────────────────

class DeadlineListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        qs = ActionDeadline.objects.filter(tenant_id=request.user.tenant_id)
        entity_type = request.query_params.get('entity_type')
        entity_id = request.query_params.get('entity_id')
        dl_status = request.query_params.get('status')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)
        if entity_id:
            qs = qs.filter(entity_id=entity_id)
        if dl_status:
            qs = qs.filter(status=dl_status)
        return success_response(data={
            'deadlines': ActionDeadlineSerializer(qs.order_by('deadline_at')[:200], many=True).data
        })

    def post(self, request):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        from datetime import timedelta
        required = ('entity_type', 'entity_id', 'action_required', 'deadline_at')
        missing = [f for f in required if not request.data.get(f)]
        if missing:
            return error_response(f'Missing required fields: {", ".join(missing)}')

        deadline = ActionDeadline.objects.create(
            tenant_id=request.user.tenant_id,
            entity_type=request.data['entity_type'],
            entity_id=request.data['entity_id'],
            action_required=request.data['action_required'],
            deadline_at=request.data['deadline_at'],
            assigned_to=request.data.get('assigned_to'),
            escalate_to=request.data.get('escalate_to'),
            metadata=request.data.get('metadata', {}),
        )
        return success_response(
            data={'deadline': ActionDeadlineSerializer(deadline).data},
            status_code=status.HTTP_201_CREATED,
        )


class DeadlineCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        deadline = ActionDeadline.objects.filter(id=pk, tenant_id=request.user.tenant_id).first()
        if not deadline:
            return error_response('Deadline not found.', status_code=status.HTTP_404_NOT_FOUND)

        if deadline.status == 'completed':
            return error_response('Deadline is already completed.')

        deadline.status = 'completed'
        deadline.completed_at = timezone.now()
        deadline.save(update_fields=['status', 'completed_at', 'updated_at'])

        return success_response(data={'deadline': ActionDeadlineSerializer(deadline).data})


class OverdueDeadlineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        now = timezone.now()
        qs = ActionDeadline.objects.filter(
            tenant_id=request.user.tenant_id,
            deadline_at__lt=now,
            status__in=['pending', 'reminded', 'escalated'],
        ).order_by('deadline_at')

        return success_response(data={
            'deadlines': ActionDeadlineSerializer(qs[:200], many=True).data,
            'count': qs.count(),
        })

class ApplicationUnifiedHistoryView(APIView):
    """
    Aggregates all candidate-related events for a specific application:
    - Stage changes
    - Interview feedback
    - Internal notes
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        
        tenant_id = request.user.tenant_id
        
        # 1. Stage History
        stage_history = ApplicationStageHistory.objects.filter(
            application_id=pk, 
            tenant_id=tenant_id
        ).order_by('-moved_at')
        
        # 2. Internal Notes
        from apps.candidates.models import CandidateNote
        notes = CandidateNote.objects.filter(
            application_id=pk, 
            tenant_id=tenant_id,
            is_deleted=False
        ).order_by('-created_at')
        
        # 3. Interview Feedback
        from apps.interviews.models import Interview, InterviewFeedback
        interviews = Interview.objects.filter(
            application_id=pk, 
            tenant_id=tenant_id,
            is_deleted=False
        )
        feedback = InterviewFeedback.objects.filter(
            interview_id__in=interviews.values('id'),
            tenant_id=tenant_id,
            is_deleted=False
        ).order_by('-submitted_at')
        
        # Combine and Normalize
        history = []
        
        for h in stage_history:
            history.append({
                'type': 'stage_change',
                'id': str(h.id),
                'timestamp': h.moved_at,
                'from_status': h.from_status,
                'to_status': h.to_status,
                'moved_by': str(h.moved_by),
                'reason': h.reason,
            })
            
        for n in notes:
            history.append({
                'type': 'note',
                'id': str(n.id),
                'timestamp': n.created_at,
                'text': n.note_text,
                'note_type': n.note_type,
                'created_by': str(n.created_by),
            })
            
        for f in feedback:
            history.append({
                'type': 'interview_feedback',
                'id': str(f.id),
                'timestamp': f.submitted_at,
                'score': f.score,
                'notes': f.notes,
                'recommendation': f.recommendation,
                'panelist_id': str(f.panelist_id),
            })
            
        # Final Sort
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return success_response(data={'history': history})

class CandidateCrossJobView(APIView):
    """
    Returns all applications for a specific candidate within the tenant.
    Used for the 'Suitcase' icon/Cross-job visibility in the profile panel.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, candidate_id):
        if is_candidate(request.user):
            return error_response(
                'You do not have permission to access pipeline operations.',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        
        tenant_id = request.user.tenant_id
        
        from apps.pipeline.models import Application
        from apps.jobs.models import JobRequisition
        from apps.pipeline.serializers import ApplicationSerializer
        
        apps = Application.objects.filter(
            candidate_id=candidate_id,
            tenant_id=tenant_id,
            is_deleted=False
        ).select_related('requisition') # assuming relational link if exists, else manual lookup
        
        # Build enriched list
        results = []
        for app in apps:
            job = JobRequisition.objects.filter(id=app.requisition_id).first()
            results.append({
                'application_id': str(app.id),
                'job_id': str(app.requisition_id),
                'job_title': job.title if job else 'Unknown Job',
                'status': app.status,
                'created_at': app.created_at,
                'is_current': False # will be set on frontend
            })
            
        return success_response(data={'applications': results})
