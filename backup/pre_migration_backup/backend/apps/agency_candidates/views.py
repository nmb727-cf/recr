from django.utils import timezone
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
try:
    from django_filters.rest_framework import DjangoFilterBackend
except Exception:
    DjangoFilterBackend = None
from apps.agency_candidates.models import (
    AgencyCandidatePipelineRegistry,
    AgencyCandidate,
    AgencyCandidateTag,
    AgencyCandidateNote,
    AgencyCandidateActivity,
    AgencyCandidateOwnership,
    AgencyCandidateHotlist,
    AgencyCandidateHotlistMember,
    AgencyCandidateResumeVersion,
    AgencyCandidateSubmission
)
from apps.agency_candidates.serializers import (
    AgencyCandidatePipelineRegistrySerializer,
    AgencyCandidateSerializer,
    AgencyCandidateTagSerializer,
    AgencyCandidateNoteSerializer,
    AgencyCandidateActivitySerializer,
    AgencyCandidateOwnershipSerializer,
    AgencyCandidateHotlistSerializer,
    AgencyCandidateHotlistMemberSerializer,
    AgencyCandidateResumeVersionSerializer,
    AgencyCandidateSubmissionSerializer
)
from apps.agency_candidates.services import AgencyCandidateCRMService

FILTER_BACKENDS = [DjangoFilterBackend] if DjangoFilterBackend else []


class AgencyCandidatePipelineRegistryViewSet(viewsets.ModelViewSet):
    queryset = AgencyCandidatePipelineRegistry.objects.all()
    serializer_class = AgencyCandidatePipelineRegistrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = FILTER_BACKENDS
    filterset_fields = ['tenant_id', 'is_active', 'is_system']


class AgencyCandidateViewSet(viewsets.ModelViewSet):
    queryset = AgencyCandidate.objects.all()
    serializer_class = AgencyCandidateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [*FILTER_BACKENDS, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tenant_id', 'status', 'owner', 'pipeline_stage', 'availability', 'source', 'is_hotlisted']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'candidate__email', 'candidate__current_title']
    ordering_fields = ['created_at', 'updated_at', 'last_contacted_at', 'expected_salary_min']

    def create(self, request, *args, **kwargs):
        # Use service for creation to handle core candidate logic
        tenant_id = request.data.get('tenant_id')
        if not tenant_id:
            return Response({'error': 'tenant_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            agency_candidate = AgencyCandidateCRMService.create_agency_candidate(
                tenant_id=tenant_id,
                candidate_data=request.data,
                recruiter_id=request.user.id
            )
            serializer = self.get_serializer(agency_candidate)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def change_stage(self, request, pk=None):
        candidate = self.get_object()
        stage_id = request.data.get('stage_id')
        if not stage_id:
            return Response({'error': 'stage_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            stage = AgencyCandidatePipelineRegistry.objects.get(id=stage_id, tenant_id=candidate.tenant_id)
        except AgencyCandidatePipelineRegistry.DoesNotExist:
            return Response({'error': 'Invalid stage_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_stage_label = candidate.pipeline_stage.stage_label if candidate.pipeline_stage else "None"
        candidate.pipeline_stage = stage
        candidate.save()
        
        # Log activity
        AgencyCandidateActivity.objects.create(
            agency_candidate=candidate,
            tenant_id=candidate.tenant_id,
            activity_type='pipeline_stage_changed',
            actor_id=request.user.id,
            payload={'old_stage': old_stage_label, 'new_stage': stage.stage_label}
        )
        
        return Response({'status': 'stage updated', 'new_stage': stage.stage_label})

    @action(detail=True, methods=['post'])
    def transfer_ownership(self, request, pk=None):
        new_owner_id = request.data.get('new_owner_id')
        if not new_owner_id:
            return Response({'error': 'new_owner_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            candidate = AgencyCandidateCRMService.transfer_ownership(
                agency_candidate_id=pk,
                new_owner_id=new_owner_id,
                actor_id=request.user.id
            )
            return Response({'status': 'ownership transferred'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        client_tenant_id = request.data.get('client_tenant_id')
        job_id = request.data.get('job_id')
        
        if not client_tenant_id or not job_id:
            return Response({'error': 'client_tenant_id and job_id are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            submission = AgencyCandidateCRMService.submit_to_client(
                agency_candidate_id=pk,
                client_tenant_id=client_tenant_id,
                job_id=job_id,
                recruiter_id=request.user.id
            )
            serializer = AgencyCandidateSubmissionSerializer(submission)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AgencyCandidateNoteViewSet(viewsets.ModelViewSet):
    queryset = AgencyCandidateNote.objects.all()
    serializer_class = AgencyCandidateNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = FILTER_BACKENDS
    filterset_fields = ['agency_candidate', 'note_type']


class AgencyCandidateHotlistViewSet(viewsets.ModelViewSet):
    queryset = AgencyCandidateHotlist.objects.all()
    serializer_class = AgencyCandidateHotlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = FILTER_BACKENDS
    filterset_fields = ['tenant_id', 'owner', 'is_private']


class AgencyCandidateHotlistMemberViewSet(viewsets.ModelViewSet):
    queryset = AgencyCandidateHotlistMember.objects.all()
    serializer_class = AgencyCandidateHotlistMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = FILTER_BACKENDS
    filterset_fields = ['hotlist']


class AgencyCandidateResumeVersionViewSet(viewsets.ModelViewSet):
    queryset = AgencyCandidateResumeVersion.objects.all()
    serializer_class = AgencyCandidateResumeVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = FILTER_BACKENDS
    filterset_fields = ['agency_candidate']


class AgencyCandidateSubmissionViewSet(viewsets.ModelViewSet):
    queryset = AgencyCandidateSubmission.objects.all()
    serializer_class = AgencyCandidateSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = FILTER_BACKENDS
    filterset_fields = ['agency_candidate', 'client_tenant_id', 'status']
