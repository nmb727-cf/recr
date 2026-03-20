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
        if Application.objects.filter(
            tenant_id=request.user.tenant_id,
            candidate_id=data['candidate_id'],
            requisition_id=data['requisition_id'],
            is_deleted=False
        ).exists():
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

        serializer = ApplicationSerializer(application, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'application': serializer.data},
            message="Application updated."
        )


class ApplicationMoveStageView(APIView):
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

        stage_id = request.data.get('stage_id')
        notes = request.data.get('notes', '')

        if not stage_id:
            return error_response("stage_id is required.")

        # Verify stage belongs to same requisition
        try:
            stage = JobStage.objects.get(
                id=stage_id,
                requisition_id=application.requisition_id,
                is_active=True
            )
        except JobStage.DoesNotExist:
            return error_response("Stage not found.", status_code=status.HTTP_404_NOT_FOUND)

        old_stage_id = application.current_stage_id
        old_status = application.status

        application.current_stage_id = stage_id
        application.status = stage.stage_type
        application.save(update_fields=['current_stage_id', 'status', 'updated_at'])

        # Record history
        ApplicationStageHistory.objects.create(
            tenant_id=request.user.tenant_id,
            application_id=application.id,
            from_stage_id=old_stage_id,
            to_stage_id=stage_id,
            from_status=old_status,
            to_status=stage.stage_type,
            moved_by=request.user.id,
            notes=notes,
        )

        # Create deadline for new stage
        ActionDeadline.objects.create(
            tenant_id=request.user.tenant_id,
            entity_type='application',
            entity_id=application.id,
            action_required=f'Take action on {stage.name} stage',
            assigned_to=request.user.id,
            deadline_at=timezone.now() + timedelta(hours=stage.action_deadline_hours),
        )

        return success_response(
            data={'application': ApplicationSerializer(application).data},
            message=f"Moved to {stage.name}."
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

        notes = request.data.get('notes', '')
        old_status = application.status

        application.status = 'shortlisted'
        application.save(update_fields=['status', 'updated_at'])

        ApplicationStageHistory.objects.create(
            tenant_id=request.user.tenant_id,
            application_id=application.id,
            from_status=old_status,
            to_status='shortlisted',
            moved_by=request.user.id,
            notes=notes,
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

        reason = request.data.get('reason', '')
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
        )

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

        reason = request.data.get('reason', '')
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
            notes=f"Offer made: {currency} {offer_amount}",
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
        application_ids = request.data.get('application_ids', [])
        action = request.data.get('action')
        data = request.data.get('data', {})

        if not application_ids or not action:
            return error_response("application_ids and action are required.")

        if action not in ['move_stage', 'reject', 'shortlist']:
            return error_response("Invalid action. Use: move_stage, reject, shortlist.")

        applications = Application.objects.filter(
            id__in=application_ids,
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        updated_count = 0
        for application in applications:
            if action == 'reject':
                application.status = 'rejected'
                application.rejection_reason = data.get('reason', '')
                application.save(update_fields=['status', 'rejection_reason', 'updated_at'])
                updated_count += 1

            elif action == 'shortlist':
                application.status = 'shortlisted'
                application.save(update_fields=['status', 'updated_at'])
                updated_count += 1

            elif action == 'move_stage':
                stage_id = data.get('stage_id')
                if stage_id:
                    application.current_stage_id = stage_id
                    application.save(update_fields=['current_stage_id', 'updated_at'])
                    updated_count += 1

        return success_response(
            data={'updated_count': updated_count},
            message=f"Bulk action '{action}' applied to {updated_count} applications."
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
