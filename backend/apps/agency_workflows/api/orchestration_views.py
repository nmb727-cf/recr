from rest_framework import viewsets, status, response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from ..models.orchestration import (
    AgencyWorkflowProcessInstance,
    AgencyInternalApprovalCheckpoint,
    AgencyClientResponseCheckpoint,
    AgencyOfferProgressCheckpoint,
    AgencyPlacementGuaranteeRecord
)
from .orchestration_serializers import (
    AgencyWorkflowProcessInstanceSerializer,
    AgencyWorkflowProcessTimelineSerializer,
    AgencyInternalApprovalCheckpointSerializer,
    AgencyClientResponseCheckpointSerializer,
    AgencyOfferProgressCheckpointSerializer,
    AgencyPlacementGuaranteeRecordSerializer
)
from ..services.agency_workflow_orchestration_engine import AgencyWorkflowOrchestrationEngine

class AgencyWorkflowOrchestrationViewSet(viewsets.ModelViewSet):
    queryset = AgencyWorkflowProcessInstance.objects.all()
    serializer_class = AgencyWorkflowProcessInstanceSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        instance = self.get_object()
        serializer = AgencyWorkflowProcessTimelineSerializer(instance)
        return response.Response(serializer.data)

    @action(detail=False, methods=['post'])
    def start(self, request):
        tenant_id = request.data.get('tenant_id')
        workflow_id = request.data.get('workflow_id')
        entity_type = request.data.get('entity_type')
        entity_id = request.data.get('entity_id')
        candidate_id = request.data.get('candidate_id')
        client_id = request.data.get('client_id')
        job_id = request.data.get('job_id')
        assigned_recruiter_id = request.data.get('assigned_recruiter_id')
        
        instance = AgencyWorkflowOrchestrationEngine.start_agency_process_instance(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            entity_type=entity_type,
            entity_id=entity_id,
            candidate_id=candidate_id,
            client_id=client_id,
            job_id=job_id,
            assigned_recruiter_id=assigned_recruiter_id
        )
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def advance(self, request, pk=None):
        instance = self.get_object()
        next_stage_key = request.data.get('next_stage_key')
        next_stage_type = request.data.get('next_stage_type')
        metadata = request.data.get('metadata', {})
        
        stage = AgencyWorkflowOrchestrationEngine.move_to_next_stage(
            instance, next_stage_key, next_stage_type, metadata
        )
        return response.Response({"status": "advanced", "current_stage": stage.stage_key})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        instance = self.get_object()
        AgencyWorkflowOrchestrationEngine.fail_agency_process_instance(instance, reason='cancelled')
        return response.Response({"status": "cancelled"})

class AgencyWorkflowApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgencyInternalApprovalCheckpoint.objects.all()
    serializer_class = AgencyInternalApprovalCheckpointSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        checkpoint = self.get_object()
        notes = request.data.get('notes')
        AgencyWorkflowOrchestrationEngine.handle_internal_approval_response(checkpoint.id, 'approved', notes)
        return response.Response({"status": "approved"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        checkpoint = self.get_object()
        notes = request.data.get('notes')
        AgencyWorkflowOrchestrationEngine.handle_internal_approval_response(checkpoint.id, 'rejected', notes)
        return response.Response({"status": "rejected"})

class AgencyClientResponseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgencyClientResponseCheckpoint.objects.all()
    serializer_class = AgencyClientResponseCheckpointSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=['post'])
    def followup(self, request, pk=None):
        checkpoint = self.get_object()
        AgencyWorkflowOrchestrationEngine.trigger_client_followup(checkpoint.id)
        return response.Response({"status": "reminded"})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        checkpoint = self.get_object()
        checkpoint.status = 'responded'
        checkpoint.save()
        
        # Advance the process
        stage = checkpoint.stage_execution
        stage.status = 'completed'
        stage.completed_at = timezone.now()
        stage.save()
        
        stage.process_instance.process_status = 'running'
        stage.process_instance.save()
        
        return response.Response({"status": "completed"})

class AgencyOfferViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgencyOfferProgressCheckpoint.objects.all()
    serializer_class = AgencyOfferProgressCheckpointSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=['post'])
    def counter(self, request, pk=None):
        checkpoint = self.get_object()
        amount = request.data.get('amount')
        AgencyWorkflowOrchestrationEngine.record_offer_progress(
            process_instance=checkpoint.process_instance,
            offer_status='countered',
            proposed_amount=amount
        )
        return response.Response({"status": "countered"})

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        checkpoint = self.get_object()
        AgencyWorkflowOrchestrationEngine.record_offer_progress(
            process_instance=checkpoint.process_instance,
            offer_status='accepted'
        )
        return response.Response({"status": "accepted"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        checkpoint = self.get_object()
        AgencyWorkflowOrchestrationEngine.record_offer_progress(
            process_instance=checkpoint.process_instance,
            offer_status='rejected'
        )
        return response.Response({"status": "rejected"})

class AgencyPlacementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgencyPlacementGuaranteeRecord.objects.all()
    serializer_class = AgencyPlacementGuaranteeRecordSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

class AgencyGuaranteeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgencyPlacementGuaranteeRecord.objects.all()
    serializer_class = AgencyPlacementGuaranteeRecordSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        # Here we could specifically filter for guarantee_status in active, breached, completed
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id, guarantee_status__in=['active', 'breached', 'completed'])
        return self.queryset.filter(guarantee_status__in=['active', 'breached', 'completed'])
