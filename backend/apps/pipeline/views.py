from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.pipeline.models import Application, ApplicationStageHistory, ActionDeadline
from apps.pipeline.serializers import (
    ApplicationSerializer, ApplicationStageHistorySerializer,
    ActionDeadlineSerializer,
)
from apps.jobs.models import JobRequisition, JobStage
from apps.candidates.models import Candidate
from apps.core.responses import success_response, error_response
from apps.core import events
from apps.candidates.pipeline_hooks import (
    on_application_created,
    on_application_stage_changed,
    on_application_rejected,
    on_offer_made,
    on_candidate_hired,
)


def _extract_stage_note(payload):
    note = (
        payload.get('note')
        or payload.get('notes')
        or payload.get('reason')
        or ''
    )
    return str(note).strip()


def _require_stage_note(payload):
    note = _extract_stage_note(payload)
    if not note:
        return None, error_response(
            "A mandatory note/reason is required for every stage change.",
            errors={'note': ['This field is required.']},
        )
    return note, None


def validate_application_move(application, target_stage, reason=None):
    """
    Validates if an application can move to the target stage.
    Returns (True, None) if valid, (False, error_message) if invalid.
    """
    from apps.interviews.models import Interview
    from apps.jobs.models import JobStage

    # 1. State Machine Enforcement (Dynamic)
    current_stage = None
    if application.current_stage_id:
        try:
            current_stage = JobStage.objects.get(id=application.current_stage_id)
        except JobStage.DoesNotExist:
            pass

    if current_stage:
        # Forward movement check
        if target_stage.stage_order > current_stage.stage_order:
            skipped_stages = JobStage.objects.filter(
                requisition_id=application.requisition_id,
                is_active=True,
                stage_order__gt=current_stage.stage_order,
                stage_order__lt=target_stage.stage_order
            ).exists()

            if skipped_stages:
                return False, f"Cannot skip stages for {application.id}. Please move through each stage in order."

        # Backward movement requirement
        elif target_stage.stage_order < current_stage.stage_order:
            if not reason:
                return False, f"A reason is required for backward stage movement of {application.id}."

    # 2. Interview Validation
    if target_stage.stage_type in ['offer', 'joined']:
        completed_interviews = Interview.objects.filter(
            application_id=application.id,
            status='completed'
        ).exists()
        if not completed_interviews:
            return False, f"Cannot move {application.id} to Offer/Hired stage without at least one completed interview."

    return True, None


def perform_application_move(application, target_stage, user, notes=None, reason=None, request=None):
    """
    Performs the actual database updates, history recording, and event emission.
    """
    from apps.jobs.models import JobRequisition, JobStage
    
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
    application.save(update_fields=['current_stage_id', 'status', 'updated_at'])

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
                if job.headcount == 0:
                    job.status = 'closed'
                    job.closed_at = timezone.now()
                    job.closed_reason = "Headcount reached"
                job.save(update_fields=['headcount', 'status', 'closed_at', 'closed_reason', 'updated_at'])
        except JobRequisition.DoesNotExist:
            pass

        # Engagement Layer Hook
        try:
            on_candidate_hired(application, user)
        except Exception:
            pass

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


class ApplicationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Application.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        # Filters
        requisition_id = request.query_params.get('requisition_id')
        if requisition_id:
            qs = qs.filter(requisition_id=requisition_id)

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        stage_id = request.query_params.get('stage_id')
        if stage_id:
            qs = qs.filter(current_stage_id=stage_id)

        agency_id = request.query_params.get('agency_id')
        if agency_id:
            qs = qs.filter(agency_id=agency_id)

        return success_response(
            data={'applications': ApplicationSerializer(qs, many=True).data},
            message="Applications retrieved.",
            meta={'total': qs.count()}
        )

    def post(self, request):
        serializer = ApplicationSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        data = serializer.validated_data

        # Check duplicate application
        existing_app = Application.objects.filter(
            tenant_id=request.user.tenant_id,
            candidate_id=data['candidate_id'],
            requisition_id=data['requisition_id'],
            is_deleted=False
        ).first()

        if existing_app:
            # Mark as duplicate attempt in metadata
            if 'duplicate_attempts' not in existing_app.metadata:
                existing_app.metadata['duplicate_attempts'] = []
            
            existing_app.metadata['duplicate_attempts'].append({
                'attempted_at': timezone.now().isoformat(),
                'attempted_by': str(request.user.id),
                'source': data.get('source', 'direct')
            })
            existing_app.save(update_fields=['metadata', 'updated_at'])

            return error_response(
                "Candidate has already applied for this job.",
                status_code=status.HTTP_409_CONFLICT
            )

        # Verify requisition belongs to tenant
        try:
            requisition = JobRequisition.objects.get(
                id=data['requisition_id'],
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Get first stage
        first_stage = JobStage.objects.filter(
            requisition_id=data['requisition_id'],
            is_active=True
        ).order_by('stage_order').first()

        application = serializer.save(
            tenant_id=request.user.tenant_id,
            submitted_by=request.user.id,
            submitted_by_tenant_id=request.user.tenant_id,
            current_stage_id=first_stage.id if first_stage else None,
            status='applied',
            created_by=request.user.id,
        )

        # Record stage history
        ApplicationStageHistory.objects.create(
            tenant_id=request.user.tenant_id,
            application_id=application.id,
            to_stage_id=first_stage.id if first_stage else None,
            to_status='applied',
            moved_by=request.user.id,
            notes='Application submitted',
        )

        # Create 24hr review deadline
        ActionDeadline.objects.create(
            tenant_id=request.user.tenant_id,
            entity_type='application',
            entity_id=application.id,
            action_required='Review new application',
            assigned_to=request.user.id,
            deadline_at=timezone.now() + timedelta(hours=24),
        )

        # Update CRM status if candidate exists in CRM pipeline
        from apps.candidates.crm_models import CandidatePipelineStatus
        CandidatePipelineStatus.objects.filter(
            tenant_id=request.user.tenant_id,
            candidate_id=data['candidate_id'],
            status__in=['ready_to_submit', 'in_process']
        ).update(
            status='submitted',
            updated_at=timezone.now()
        )

        # Engagement Layer Hook
        try:
            on_application_created(application, request.user)
        except Exception:
            pass

        # Emit Event
        events.application.created.send(
            sender=self.__class__,
            application=application,
            user=request.user,
            request=request
        )

        return success_response(

            data={'application': ApplicationSerializer(application).data},
            message="Application created.",
            status_code=status.HTTP_201_CREATED
        )


class ApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return Application.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Application.DoesNotExist:
            return None

    def get(self, request, pk):
        application = self.get_object(request, pk)
        if not application:
            return error_response("Application not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Get stage history
        history = ApplicationStageHistory.objects.filter(
            application_id=pk
        ).order_by('moved_at')

        return success_response(
            data={
                'application': ApplicationSerializer(application).data,
                'stage_history': ApplicationStageHistorySerializer(history, many=True).data,
            },
            message="Application retrieved."
        )

    def put(self, request, pk):
        application = self.get_object(request, pk)
        if not application:
            return error_response("Application not found.", status_code=status.HTTP_404_NOT_FOUND)

        old_status = application.status
        old_stage_id = application.current_stage_id
        stage_change_requested = (
            ('status' in request.data and request.data.get('status') != old_status) or
            ('current_stage_id' in request.data and request.data.get('current_stage_id') != str(old_stage_id))
        )
        if stage_change_requested:
            stage_note, note_error = _require_stage_note(request.data)
            if note_error:
                return note_error
        else:
            stage_note = None

        serializer = ApplicationSerializer(application, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        updated_application = serializer.save()
        if stage_change_requested:
            ApplicationStageHistory.objects.create(
                tenant_id=request.user.tenant_id,
                application_id=updated_application.id,
                from_stage_id=old_stage_id,
                to_stage_id=updated_application.current_stage_id,
                from_status=old_status,
                to_status=updated_application.status,
                moved_by=request.user.id,
                reason=stage_note,
                notes=stage_note,
                metadata={
                    'previous_stage': old_status,
                    'new_stage': updated_application.status,
                    'note': stage_note,
                    'changed_by': str(request.user.id),
                    'changed_at': timezone.now().isoformat(),
                    'source': 'application_detail_put',
                },
            )
            try:
                on_application_stage_changed(
                    updated_application,
                    old_status,
                    updated_application.status,
                    request.user,
                    note=stage_note,
                )
            except Exception:
                pass
        return success_response(
            data={'application': serializer.data},
            message="Application updated."
        )


class ApplicationMoveStageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from apps.jobs.models import JobStage

        try:
            application = Application.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Application.DoesNotExist:
            return error_response("Application not found.", status_code=status.HTTP_404_NOT_FOUND)

        stage_id = request.data.get('stage_id')
        stage_note, note_error = _require_stage_note(request.data)
        if note_error:
            return note_error

        if not stage_id:
            return error_response("stage_id is required.")

        # Verify stage
        try:
            target_stage = JobStage.objects.get(
                id=stage_id,
                requisition_id=application.requisition_id,
                is_active=True
            )
        except JobStage.DoesNotExist:
            return error_response("Target stage not found.", status_code=status.HTTP_404_NOT_FOUND)

        # 1. Validate Move
        is_valid, error_msg = validate_application_move(application, target_stage, stage_note)
        if not is_valid:
            return error_response(error_msg)

        # 2. Perform Move
        old_status = application.status
        application = perform_application_move(
            application, target_stage, request.user, 
            notes=stage_note, reason=stage_note, request=request
        )

        # Engagement Layer Hook
        try:
            on_application_stage_changed(
                application,
                old_status,
                application.status,
                request.user,
                note=stage_note,
            )
        except Exception:
            pass

        return success_response(
            data={'application': ApplicationSerializer(application).data},
            message=f"Moved to {target_stage.name}."
        )


class ApplicationShortlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            application = Application.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Application.DoesNotExist:
            return error_response("Application not found.", status_code=status.HTTP_404_NOT_FOUND)

        stage_note, note_error = _require_stage_note(request.data)
        if note_error:
            return note_error
        old_status = application.status

        application.status = 'shortlisted'
        application.save(update_fields=['status', 'updated_at'])

        ApplicationStageHistory.objects.create(
            tenant_id=request.user.tenant_id,
            application_id=application.id,
            from_status=old_status,
            to_status='shortlisted',
            moved_by=request.user.id,
            reason=stage_note,
            notes=stage_note,
            metadata={
                'previous_stage': old_status,
                'new_stage': 'shortlisted',
                'note': stage_note,
                'changed_by': str(request.user.id),
                'changed_at': timezone.now().isoformat(),
            },
        )

        # 48hr deadline to schedule interview
        ActionDeadline.objects.create(
            tenant_id=request.user.tenant_id,
            entity_type='application',
            entity_id=application.id,
            action_required='Schedule interview for shortlisted candidate',
            assigned_to=request.user.id,
            deadline_at=timezone.now() + timedelta(hours=48),
        )

        # Emit Event
        events.application.shortlisted.send(
            sender=self.__class__,
            application=application,
            user=request.user,
            request=request
        )

        return success_response(
            data={'application': ApplicationSerializer(application).data},
            message="Candidate shortlisted."
        )


class ApplicationRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            application = Application.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Application.DoesNotExist:
            return error_response("Application not found.", status_code=status.HTTP_404_NOT_FOUND)

        stage_note, note_error = _require_stage_note(request.data)
        if note_error:
            return note_error
        reason = stage_note
        category = request.data.get('category', '')
        old_status = application.status

        application.status = 'rejected'
        application.rejection_reason = reason
        application.rejection_category = category
        application.save(update_fields=['status', 'rejection_reason', 'rejection_category', 'updated_at'])

        ApplicationStageHistory.objects.create(
            tenant_id=request.user.tenant_id,
            application_id=application.id,
            from_status=old_status,
            to_status='rejected',
            moved_by=request.user.id,
            reason=reason,
            notes=stage_note,
            metadata={
                'previous_stage': old_status,
                'new_stage': 'rejected',
                'note': stage_note,
                'changed_by': str(request.user.id),
                'changed_at': timezone.now().isoformat(),
            },
        )

        # Engagement Layer Hook
        try:
            on_application_rejected(application, reason, request.user)
        except Exception:
            pass

        return success_response(
            data={'application': ApplicationSerializer(application).data},
            message="Application rejected."
        )


class ApplicationWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            application = Application.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Application.DoesNotExist:
            return error_response("Application not found.", status_code=status.HTTP_404_NOT_FOUND)

        stage_note, note_error = _require_stage_note(request.data)
        if note_error:
            return note_error
        reason = stage_note
        old_status = application.status

        application.status = 'withdrawn'
        application.withdrawn_reason = reason
        application.save(update_fields=['status', 'withdrawn_reason', 'updated_at'])

        ApplicationStageHistory.objects.create(
            tenant_id=request.user.tenant_id,
            application_id=application.id,
            from_status=old_status,
            to_status='withdrawn',
            moved_by=request.user.id,
            reason=reason,
            notes=stage_note,
            metadata={
                'previous_stage': old_status,
                'new_stage': 'withdrawn',
                'note': stage_note,
                'changed_by': str(request.user.id),
                'changed_at': timezone.now().isoformat(),
            },
        )

        return success_response(
            data={'application': ApplicationSerializer(application).data},
            message="Application withdrawn."
        )


class ApplicationMakeOfferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            application = Application.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Application.DoesNotExist:
            return error_response("Application not found.", status_code=status.HTTP_404_NOT_FOUND)

        offer_amount = request.data.get('offer_amount')
        currency = request.data.get('currency', 'INR')
        joining_date = request.data.get('joining_date')

        if not offer_amount:
            return error_response("offer_amount is required.")
        stage_note, note_error = _require_stage_note(request.data)
        if note_error:
            return note_error

        old_status = application.status

        application.status = 'offer'
        application.offer_amount = offer_amount
        application.offer_currency = currency
        application.offer_date = timezone.now().date()
        if joining_date:
            application.joining_date = joining_date
        application.save(update_fields=[
            'status', 'offer_amount', 'offer_currency',
            'offer_date', 'joining_date', 'updated_at'
        ])

        ApplicationStageHistory.objects.create(
            tenant_id=request.user.tenant_id,
            application_id=application.id,
            from_status=old_status,
            to_status='offer',
            moved_by=request.user.id,
            reason=stage_note,
            notes=stage_note,
            metadata={
                'previous_stage': old_status,
                'new_stage': 'offer',
                'note': stage_note,
                'changed_by': str(request.user.id),
                'changed_at': timezone.now().isoformat(),
                'offer_amount': str(offer_amount),
                'offer_currency': currency,
            },
        )

        # 48hr deadline for candidate response
        ActionDeadline.objects.create(
            tenant_id=request.user.tenant_id,
            entity_type='offer',
            entity_id=application.id,
            action_required='Follow up on offer response',
            assigned_to=request.user.id,
            deadline_at=timezone.now() + timedelta(hours=48),
        )

        # Engagement Layer Hook
        try:
            on_offer_made(application, request.data, request.user)
        except Exception:
            pass

        # Emit Event
        events.application.offer_made.send(
            sender=self.__class__,
            application=application,
            user=request.user,
            request=request
        )

        return success_response(
            data={'application': ApplicationSerializer(application).data},
            message="Offer made."
        )


class PipelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, requisition_id):
        # Verify requisition belongs to tenant
        try:
            JobRequisition.objects.get(
                id=requisition_id,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Get all stages
        stages = JobStage.objects.filter(
            requisition_id=requisition_id,
            is_active=True
        ).order_by('stage_order')

        # Get all applications for this requisition
        applications = Application.objects.filter(
            requisition_id=requisition_id,
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        # Group applications by stage
        applications_by_stage = {}
        for stage in stages:
            stage_apps = applications.filter(current_stage_id=stage.id)
            applications_by_stage[str(stage.id)] = {
                'stage': {
                    'id': str(stage.id),
                    'name': stage.name,
                    'stage_type': stage.stage_type,
                    'stage_order': stage.stage_order,
                },
                'applications': ApplicationSerializer(stage_apps, many=True).data,
                'count': stage_apps.count(),
            }

        return success_response(
            data={
                'requisition_id': requisition_id,
                'pipeline': applications_by_stage,
                'total_applications': applications.count(),
            },
            message="Pipeline retrieved."
        )


class BulkActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.jobs.models import JobStage
        
        application_ids = request.data.get('application_ids', [])
        action = request.data.get('action')
        data = request.data.get('data', {})

        if not application_ids or not action:
            return error_response("application_ids and action are required.")

        if action not in ['move_stage', 'reject', 'shortlist']:
            return error_response("Invalid action. Use: move_stage, reject, shortlist.")
        stage_note, note_error = _require_stage_note(data)
        if note_error:
            return note_error

        applications = Application.objects.filter(
            id__in=application_ids,
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        target_stage = None
        if action == 'move_stage':
            stage_id = data.get('stage_id')
            if not stage_id:
                return error_response("stage_id is required for move_stage action.")
            try:
                target_stage = JobStage.objects.get(id=stage_id, tenant_id=request.user.tenant_id)
            except JobStage.DoesNotExist:
                return error_response("Target stage not found.")

        updated_count = 0
        errors = []

        for application in applications:
            try:
                if action == 'reject':
                    old_status = application.status
                    application.status = 'rejected'
                    application.rejection_reason = stage_note
                    application.save(update_fields=['status', 'rejection_reason', 'updated_at'])
                    ApplicationStageHistory.objects.create(
                        tenant_id=request.user.tenant_id,
                        application_id=application.id,
                        from_status=old_status,
                        to_status='rejected',
                        moved_by=request.user.id,
                        reason=stage_note,
                        notes=stage_note,
                        metadata={
                            'previous_stage': old_status,
                            'new_stage': 'rejected',
                            'note': stage_note,
                            'changed_by': str(request.user.id),
                            'changed_at': timezone.now().isoformat(),
                            'bulk': True,
                        },
                    )
                    try:
                        on_application_rejected(application, stage_note, request.user)
                    except Exception:
                        pass
                    updated_count += 1

                elif action == 'shortlist':
                    old_status = application.status
                    application.status = 'shortlisted'
                    application.save(update_fields=['status', 'updated_at'])
                    ApplicationStageHistory.objects.create(
                        tenant_id=request.user.tenant_id,
                        application_id=application.id,
                        from_status=old_status,
                        to_status='shortlisted',
                        moved_by=request.user.id,
                        reason=stage_note,
                        notes=stage_note,
                        metadata={
                            'previous_stage': old_status,
                            'new_stage': 'shortlisted',
                            'note': stage_note,
                            'changed_by': str(request.user.id),
                            'changed_at': timezone.now().isoformat(),
                            'bulk': True,
                        },
                    )
                    events.application.shortlisted.send(sender=self.__class__, application=application, user=request.user, request=request)
                    updated_count += 1

                elif action == 'move_stage' and target_stage:
                    # ENFORCE VALIDATION IN BULK
                    is_valid, error_msg = validate_application_move(application, target_stage, reason=stage_note)
                    if is_valid:
                        old_status = application.status
                        perform_application_move(
                            application, target_stage, request.user, 
                            notes=stage_note, reason=stage_note, request=request
                        )
                        try:
                            refreshed = Application.objects.get(id=application.id)
                            on_application_stage_changed(refreshed, old_status, refreshed.status, request.user, note=stage_note)
                        except Exception:
                            pass
                        updated_count += 1
                    else:
                        errors.append(error_msg)
            except Exception as e:
                errors.append(f"Error processing {application.id}: {str(e)}")

        return success_response(
            data={
                'updated_count': updated_count,
                'errors': errors
            },
            message=f"Bulk action '{action}' processed. {updated_count} applications updated."
        )


class DeadlineListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ActionDeadline.objects.filter(
            tenant_id=request.user.tenant_id,
            assigned_to=request.user.id,
        )

        status_filter = request.query_params.get('status', 'pending')
        if status_filter:
            qs = qs.filter(status=status_filter)

        overdue = request.query_params.get('overdue')
        if overdue == 'true':
            qs = qs.filter(deadline_at__lt=timezone.now(), status='pending')

        return success_response(
            data={'deadlines': ActionDeadlineSerializer(qs, many=True).data},
            message="Deadlines retrieved.",
            meta={'total': qs.count()}
        )


class DeadlineCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            deadline = ActionDeadline.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
            )
        except ActionDeadline.DoesNotExist:
            return error_response("Deadline not found.", status_code=status.HTTP_404_NOT_FOUND)

        deadline.status = 'completed'
        deadline.completed_at = timezone.now()
        deadline.save(update_fields=['status', 'completed_at', 'updated_at'])

        return success_response(
            data={'deadline': ActionDeadlineSerializer(deadline).data},
            message="Deadline marked complete."
        )


class OverdueDeadlineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        overdue = ActionDeadline.objects.filter(
            tenant_id=request.user.tenant_id,
            deadline_at__lt=timezone.now(),
            status='pending'
        )
        return success_response(
            data={'deadlines': ActionDeadlineSerializer(overdue, many=True).data},
            message="Overdue deadlines retrieved.",
            meta={'total': overdue.count()}
        )
