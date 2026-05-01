from rest_framework import viewsets, status, response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from apps.orchestration_center.models.orchestration_engine import (
    WorkflowProcessInstance,
    WorkflowApprovalCheckpoint,
    WorkflowSchedulerCheckpoint,
    WorkflowNegotiationCheckpoint,
    WorkflowHandoffRecord
)
from apps.orchestration_center.api.orchestration_serializers import (
    WorkflowProcessInstanceSerializer,
    WorkflowProcessTimelineSerializer,
    WorkflowApprovalCheckpointSerializer,
    WorkflowSchedulerCheckpointSerializer,
    WorkflowNegotiationCheckpointSerializer,
    WorkflowHandoffRecordSerializer
)
from apps.orchestration_center.services.workflow_orchestration_engine import WorkflowOrchestrationEngine

class WorkflowOrchestrationViewSet(viewsets.ModelViewSet):
    queryset = WorkflowProcessInstance.objects.all()
    serializer_class = WorkflowProcessInstanceSerializer

    def get_queryset(self):
        # Basic tenant filtering
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        instance = self.get_object()
        serializer = WorkflowProcessTimelineSerializer(instance)
        return response.Response(serializer.data)

    @action(detail=False, methods=['post'])
    def start(self, request):
        tenant_id = request.data.get('tenant_id')
        workflow_id = request.data.get('workflow_id')
        entity_type = request.data.get('entity_type')
        entity_id = request.data.get('entity_id')
        
        instance = WorkflowOrchestrationEngine.start_process_instance(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            entity_type=entity_type,
            entity_id=entity_id,
            created_by=request.user.id if request.user.is_authenticated else None
        )
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def advance(self, request, pk=None):
        instance = self.get_object()
        next_stage_key = request.data.get('next_stage_key')
        next_stage_type = request.data.get('next_stage_type')
        metadata = request.data.get('metadata', {})
        
        stage = WorkflowOrchestrationEngine.move_to_next_stage(
            instance, next_stage_key, next_stage_type, metadata
        )
        return response.Response({"status": "advanced", "current_stage": stage.stage_key})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        instance = self.get_object()
        WorkflowOrchestrationEngine.fail_process_instance(instance, reason='cancelled')
        return response.Response({"status": "cancelled"})

class WorkflowApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowApprovalCheckpoint.objects.all()
    serializer_class = WorkflowApprovalCheckpointSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        checkpoint = self.get_object()
        notes = request.data.get('notes')
        WorkflowOrchestrationEngine.handle_approval_response(checkpoint.id, 'approved', notes)
        return response.Response({"status": "approved"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        checkpoint = self.get_object()
        notes = request.data.get('notes')
        WorkflowOrchestrationEngine.handle_approval_response(checkpoint.id, 'rejected', notes)
        return response.Response({"status": "rejected"})

class WorkflowSchedulingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowSchedulerCheckpoint.objects.all()
    serializer_class = WorkflowSchedulerCheckpointSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=['post'], url_path='check-availability')
    def check_availability(self, request, pk=None):
        checkpoint = self.get_object()
        # Simulated logic
        checkpoint.status = 'availability_checked'
        checkpoint.save()
        return response.Response({"status": "availability_checked"})

    @action(detail=True, methods=['post'])
    def book(self, request, pk=None):
        checkpoint = self.get_object()
        slot_data = request.data.get('slot_data')
        WorkflowOrchestrationEngine.book_scheduler_slot(checkpoint.id, slot_data)
        return response.Response({"status": "booked"})

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        checkpoint = self.get_object()
        checkpoint.status = 'reschedule_required'
        checkpoint.save()
        return response.Response({"status": "reschedule_required"})

class WorkflowNegotiationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowNegotiationCheckpoint.objects.all()
    serializer_class = WorkflowNegotiationCheckpointSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=['post'])
    def counter(self, request, pk=None):
        checkpoint = self.get_object()
        amount = request.data.get('amount')
        checkpoint.proposed_amount = amount
        checkpoint.negotiation_round += 1
        checkpoint.save()
        status_val = WorkflowOrchestrationEngine.evaluate_negotiation_band(checkpoint.id)
        return response.Response({"status": status_val, "round": checkpoint.negotiation_round})

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        checkpoint = self.get_object()
        WorkflowOrchestrationEngine.complete_negotiation(checkpoint.id, 'accepted')
        return response.Response({"status": "accepted"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        checkpoint = self.get_object()
        WorkflowOrchestrationEngine.complete_negotiation(checkpoint.id, 'rejected')
        return response.Response({"status": "rejected"})

class WorkflowHandoffViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowHandoffRecord.objects.all()
    serializer_class = WorkflowHandoffRecordSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        record = self.get_object()
        # Simulated logic
        record.status = 'sent'
        record.save()
        return response.Response({"status": "sent"})
