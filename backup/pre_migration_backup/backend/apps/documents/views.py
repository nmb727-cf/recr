from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.documents.models import Document, OfferLetter
from apps.documents.serializers import DocumentSerializer, OfferLetterSerializer
from apps.core.responses import success_response, error_response
from apps.core import events


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Document.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        entity_type = request.query_params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        entity_id = request.query_params.get('entity_id')
        if entity_id:
            qs = qs.filter(entity_id=entity_id)

        document_type = request.query_params.get('document_type')
        if document_type:
            qs = qs.filter(document_type=document_type)

        return success_response(
            data={'documents': DocumentSerializer(qs, many=True).data},
            message="Documents retrieved.",
            meta={'total': qs.count()}
        )

    def post(self, request):
        serializer = DocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        document = serializer.save(
            tenant_id=request.user.tenant_id,
            uploaded_by=request.user.id,
            created_by=request.user.id,
        )
        return success_response(
            data={'document': DocumentSerializer(document).data},
            message="Document uploaded.",
            status_code=status.HTTP_201_CREATED
        )


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return Document.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Document.DoesNotExist:
            return None

    def get(self, request, pk):
        document = self.get_object(request, pk)
        if not document:
            return error_response("Document not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'document': DocumentSerializer(document).data},
            message="Document retrieved."
        )

    def delete(self, request, pk):
        document = self.get_object(request, pk)
        if not document:
            return error_response("Document not found.", status_code=status.HTTP_404_NOT_FOUND)
        document.soft_delete()
        return success_response(
            message="Document deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )


class DocumentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        document = Document.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False
        ).first()
        if not document:
            return error_response("Document not found.", status_code=status.HTTP_404_NOT_FOUND)

        # TODO: Generate presigned MinIO URL
        return success_response(
            data={
                'download_url': document.file_url,
                'filename': document.filename,
                'expires_at': None,
            },
            message="Download URL generated."
        )


class OfferLetterListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = OfferLetter.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        application_id = request.query_params.get('application_id')
        if application_id:
            qs = qs.filter(application_id=application_id)

        return success_response(
            data={'offers': OfferLetterSerializer(qs, many=True).data},
            message="Offer letters retrieved.",
            meta={'total': qs.count()}
        )

    def post(self, request):
        serializer = OfferLetterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        metadata = dict(request.data.get('metadata') or {})
        metadata.setdefault('offer_context', {})
        metadata['offer_context'].update(
            {
                'job_id': request.data.get('job') or request.data.get('job_id') or '',
                'location': request.data.get('location', ''),
                'employment_type': request.data.get('employment_type', ''),
                'notes': request.data.get('notes', ''),
            }
        )
        metadata.setdefault('approval_flow', {'mode': 'none', 'required_approvals': 0, 'approvals': [], 'human_tasks': []})
        metadata.setdefault('negotiation', {'rounds': []})

        offer = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            status='draft',
            title=request.data.get('title') or 'Offer Letter',
            metadata=metadata,
        )
        events.offer.created.send(sender=self.__class__, offer=offer)
        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer letter created.",
            status_code=status.HTTP_201_CREATED
        )


class OfferLetterDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return OfferLetter.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except OfferLetter.DoesNotExist:
            return None

    def get(self, request, pk):
        offer = self.get_object(request, pk)
        if not offer:
            return error_response("Offer letter not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer letter retrieved."
        )


class OfferLetterSendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk, tenant_id=request.user.tenant_id, is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer letter not found.", status_code=status.HTTP_404_NOT_FOUND)

        if offer.status not in ['draft', 'approved', 'approval_pending', 'pending_approval']:
            return error_response("Only draft or approved offers can be sent.")
        if offer.status in ['approval_pending', 'pending_approval']:
            return error_response("Offer is still pending approvals.")

        offer.status = 'sent'
        offer.sent_at = timezone.now()
        offer.save(update_fields=['status', 'sent_at', 'updated_at'])
        _sync_application_offer_fields(offer=offer, request=request, app_status='offer')
        events.offer.sent.send(sender=self.__class__, application=_build_offer_application_proxy(offer))

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer letter sent."
        )


class OfferLetterApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk, tenant_id=request.user.tenant_id, is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer letter not found.", status_code=status.HTTP_404_NOT_FOUND)

        metadata = dict(offer.metadata or {})
        approval_flow = dict(metadata.get('approval_flow') or {})
        mode = str(approval_flow.get('mode') or 'single')
        required_approvals = int(approval_flow.get('required_approvals') or (1 if mode != 'none' else 0))
        approval_role = str(request.data.get('approval_role') or request.user.role or 'hiring_manager')
        approvals = list(approval_flow.get('approvals') or [])
        approval_entry = {
            'approved_by': str(request.user.id),
            'approval_role': approval_role,
            'approved_at': timezone.now().isoformat(),
            'notes': request.data.get('notes', ''),
        }
        approvals.append(approval_entry)
        dedup = {(item.get('approved_by'), item.get('approval_role')): item for item in approvals}
        approvals = list(dedup.values())
        approval_flow.update(
            {
                'mode': mode,
                'required_approvals': required_approvals,
                'approvals': approvals,
                'approved_count': len(approvals),
            }
        )
        metadata['approval_flow'] = approval_flow
        offer.metadata = metadata

        if mode == 'none' or len(approvals) >= max(required_approvals, 1):
            offer.status = 'approved'
            offer.approved_by = request.user.id
            offer.approved_at = timezone.now()
            offer.save(update_fields=['status', 'approved_by', 'approved_at', 'metadata', 'updated_at'])
            events.offer.approved.send(sender=self.__class__, offer=offer)
            message_text = "Offer letter approved."
        else:
            offer.status = 'approval_pending'
            offer.save(update_fields=['status', 'metadata', 'updated_at'])
            message_text = "Approval recorded. Awaiting remaining approvals."

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message=message_text
        )


class OfferLetterRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk, tenant_id=request.user.tenant_id, is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer letter not found.", status_code=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', '')
        offer.status = 'withdrawn'
        offer.revoked_at = timezone.now()
        offer.revoke_reason = reason
        offer.save(update_fields=['status', 'revoked_at', 'revoke_reason', 'updated_at'])
        _sync_application_offer_fields(offer=offer, request=request, app_status='withdrawn')

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer letter revoked."
        )


class OfferLetterSubmitApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk, tenant_id=request.user.tenant_id, is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer letter not found.", status_code=status.HTTP_404_NOT_FOUND)
        if offer.status not in ['draft', 'approval_pending', 'pending_approval']:
            return error_response("Only draft offers can be submitted for approval.")

        mode = str(request.data.get('mode') or 'single').strip().lower()
        if mode not in {'none', 'single', 'multi'}:
            return error_response("mode must be one of: none, single, multi.")

        roles = request.data.get('roles') or []
        if not isinstance(roles, list):
            return error_response("roles must be a list.")
        if mode == 'single' and not roles:
            roles = ['hiring_manager']
        if mode == 'multi' and not roles:
            roles = ['hiring_manager', 'finance', 'hr']

        required_approvals = int(request.data.get('required_approvals') or (len(roles) if mode == 'multi' else (1 if mode == 'single' else 0)))
        metadata = dict(offer.metadata or {})
        human_tasks = [
            {
                'task_type': 'approval',
                'title': f'{role.replace("_", " ").title()} Approval',
                'assigned_role': role,
                'status': 'pending',
            }
            for role in roles
        ]
        metadata['approval_flow'] = {
            'mode': mode,
            'required_approvals': required_approvals,
            'roles': roles,
            'approvals': [],
            'approved_count': 0,
            'human_tasks': human_tasks,
            'submitted_at': timezone.now().isoformat(),
        }
        offer.metadata = metadata
        offer.status = 'approved' if mode == 'none' else 'approval_pending'
        offer.save(update_fields=['status', 'metadata', 'updated_at'])
        _create_offer_approval_human_task(offer=offer)

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer approval flow initialized."
        )


class OfferLetterNegotiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk, tenant_id=request.user.tenant_id, is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer letter not found.", status_code=status.HTTP_404_NOT_FOUND)

        counter_salary = request.data.get('counter_salary')
        notes = request.data.get('notes', '')
        round_number = int(request.data.get('negotiation_round') or 1)

        metadata = dict(offer.metadata or {})
        negotiation = dict(metadata.get('negotiation') or {})
        rounds = list(negotiation.get('rounds') or [])
        rounds.append(
            {
                'round': round_number,
                'counter_salary': counter_salary,
                'notes': notes,
                'updated_by': str(request.user.id),
                'updated_at': timezone.now().isoformat(),
            }
        )
        negotiation['rounds'] = rounds
        negotiation['latest_counter_salary'] = counter_salary
        negotiation['latest_notes'] = notes
        negotiation['latest_round'] = round_number
        metadata['negotiation'] = negotiation
        offer.metadata = metadata
        offer.status = 'negotiation'
        offer.save(update_fields=['status', 'metadata', 'updated_at'])

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer negotiation updated."
        )


class CandidateOfferAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk,
            candidate_id=request.user.id,
            status='sent',
            is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer not found.", status_code=status.HTTP_404_NOT_FOUND)

        offer.status = 'accepted'
        offer.accepted_at = timezone.now()
        offer.save(update_fields=['status', 'accepted_at', 'updated_at'])
        events.offer.accepted.send(sender=self.__class__, application=_build_offer_application_proxy(offer))

        # ─── Hiring Completion Logic ───
        from apps.pipeline.models import Application
        from apps.jobs.models import JobRequisition, JobStage
        from apps.pipeline.views import perform_application_move
        from apps.jobs.workflow_service import JobWorkflowService

        application = Application.objects.filter(id=offer.application_id).first()
        if application:
            requisition = JobRequisition.objects.filter(id=application.requisition_id).first()
            if requisition:
                # 1. Move to joined stage
                target_stage = JobStage.objects.filter(
                    requisition_id=requisition.id, 
                    stage_type='joined'
                ).first()
                if target_stage:
                    try:
                        perform_application_move(
                            application, target_stage, request.user, 
                            notes="Offer accepted. Marking as hired."
                        )
                    except Exception:
                        pass # Non-fatal if move fails

                # 2. Trigger Workflow Event
                JobWorkflowService.trigger_job_workflow(
                    requisition=requisition,
                    event_type='hiring.complete',
                    context={
                        'application_id': str(application.id),
                        'candidate_id': str(application.candidate_id),
                        'offer_id': str(offer.id),
                    }
                )

                # 3. Auto-close check
                if requisition.auto_close_on_headcount_met and requisition.headcount <= 0:
                    requisition.status = 'closed'
                    requisition.closed_at = timezone.now()
                    requisition.closed_reason = "Headcount filled"
                    requisition.save(update_fields=['status', 'closed_at', 'closed_reason', 'updated_at'])

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer accepted. Congratulations!"
        )


class CandidateOfferRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk,
            candidate_id=request.user.id,
            status='sent',
            is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer not found.", status_code=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', '')
        offer.status = 'rejected'
        offer.rejected_at = timezone.now()
        offer.rejection_reason = reason
        offer.save(update_fields=['status', 'rejected_at', 'rejection_reason', 'updated_at'])
        _sync_application_offer_fields(offer=offer, request=request, app_status='rejected')
        events.offer.rejected.send(sender=self.__class__, application=_build_offer_application_proxy(offer))

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer rejected."
        )


def _build_offer_application_proxy(offer):
    return type(
        'OfferApplicationProxy',
        (),
        {
            'id': offer.application_id,
            'tenant_id': offer.tenant_id,
            'candidate_id': offer.candidate_id,
        },
    )()


def _sync_application_offer_fields(*, offer, request, app_status):
    from apps.pipeline.models import Application, ApplicationStageHistory

    application = Application.objects.filter(id=offer.application_id, tenant_id=request.user.tenant_id).first()
    if not application:
        return

    old_status = application.status
    if app_status:
        application.status = app_status
    if offer.offered_salary is not None:
        application.offer_amount = offer.offered_salary
    if offer.currency:
        application.offer_currency = offer.currency
    if offer.sent_at:
        application.offer_date = offer.sent_at.date()
    if offer.joining_date:
        application.joining_date = offer.joining_date
    if offer.accepted_at:
        application.offer_accepted_at = offer.accepted_at
    if offer.rejected_at:
        application.offer_rejected_at = offer.rejected_at
    application.save(
        update_fields=[
            'status',
            'offer_amount',
            'offer_currency',
            'offer_date',
            'joining_date',
            'offer_accepted_at',
            'offer_rejected_at',
            'updated_at',
        ]
    )

    ApplicationStageHistory.objects.create(
        tenant_id=request.user.tenant_id,
        application_id=application.id,
        from_stage_id=application.current_stage_id,
        to_stage_id=application.current_stage_id,
        from_status=old_status,
        to_status=application.status,
        moved_by=request.user.id,
        reason=f"Offer status changed to {offer.status}",
        notes=f"Offer {offer.id} state update via documents module.",
    )


def _create_offer_approval_human_task(*, offer):
    try:
        from apps.workflow_execution.models import WorkflowHumanTask, WorkflowInstance
        from apps.workflow_execution.services.workflow_human_task_engine import WorkflowHumanTaskEngine
    except Exception:
        return

    instance = WorkflowInstance.objects.filter(
        tenant_id=offer.tenant_id,
        entity_type='application',
        entity_id=offer.application_id,
        status__in=['running', 'waiting', 'paused'],
        is_deleted=False,
    ).order_by('-created_at').first()
    if not instance:
        return

    title = f'Offer approval pending: {offer.title}'
    already_open = WorkflowHumanTask.objects.filter(
        tenant_id=offer.tenant_id,
        workflow_instance=instance,
        title=title,
        status__in=['pending', 'in_progress'],
        is_deleted=False,
    ).exists()
    if already_open:
        return

    WorkflowHumanTaskEngine.create_human_task(
        workflow_instance=instance,
        stage_execution=instance.stage_executions.order_by('-created_at').first(),
        task_type='approval',
        title=title,
        description='Offer approval flow is pending and requires action.',
        assigned_to_type='hiring_manager',
        priority='high',
        due_at=timezone.now() + timedelta(hours=24),
        wait_for_completion=False,
        metadata={'offer_id': str(offer.id), 'task_category': 'offer_approval'},
    )
