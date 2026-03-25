from django.db.models import Count
from django.utils.text import slugify
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.core.responses import success_response, error_response
from apps.core import events
from .models import TalentPool, CandidateTalentPoolMembership
from .serializers import (
    TalentPoolSerializer, 
    CandidateTalentPoolMembershipSerializer,
    BulkAddCandidateSerializer
)

class TalentPoolViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TalentPoolSerializer
    queryset = TalentPool.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return self.queryset.filter(
            tenant_id=self.request.user.tenant_id,
            is_active=True
        ).annotate(member_count=Count('memberships'))

    def perform_create(self, serializer):
        # Infer tenant type from role
        tenant_type = 'company'
        if self.request.user.role and self.request.user.role.startswith('agency_'):
            tenant_type = 'agency'
            
        instance = serializer.save(
            tenant_id=self.request.user.tenant_id,
            tenant_type=tenant_type,
            created_by=self.request.user.id
        )
        
        # Emit event
        events.talent_pool.created.send(
            sender=self.__class__,
            talent_pool=instance,
            user=self.request.user,
            request=self.request
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data={'talent_pools': serializer.data},
            message="Talent pools retrieved."
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data={'talent_pool': serializer.data},
            message="Talent pool detail retrieved."
        )

    @action(detail=True, methods=['post'], url_path='bulk-add')
    def bulk_add_candidates(self, request, pk=None):
        talent_pool = self.get_object()
        serializer = BulkAddCandidateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        
        candidate_ids = serializer.validated_data['candidate_ids']
        note = serializer.validated_data.get('note', '')
        source = serializer.validated_data.get('source', 'manual')
        
        added_count = 0
        for candidate_id in candidate_ids:
            membership, created = CandidateTalentPoolMembership.objects.get_or_create(
                talent_pool=talent_pool,
                candidate_id=candidate_id,
                tenant_id=request.user.tenant_id,
                defaults={
                    'added_by': request.user.id,
                    'note': note,
                    'source': source
                }
            )
            if created:
                added_count += 1
                # Emit event
                events.candidate.added_to_pool.send(
                    sender=self.__class__,
                    membership=membership,
                    user=request.user,
                    request=request
                )
        
        return success_response(
            data={'added_count': added_count},
            message=f"{added_count} candidates added to pool."
        )

    @action(detail=True, methods=['post'], url_path='bulk-remove')
    def bulk_remove_candidates(self, request, pk=None):
        talent_pool = self.get_object()
        candidate_ids = request.data.get('candidate_ids', [])
        
        if not isinstance(candidate_ids, list):
            return error_response("candidate_ids must be a list.")
            
        memberships = CandidateTalentPoolMembership.objects.filter(
            talent_pool=talent_pool,
            candidate_id__in=candidate_ids,
            tenant_id=request.user.tenant_id
        )
        
        removed_count = 0
        for membership in memberships:
            candidate = membership.candidate
            membership.delete()
            removed_count += 1
            # Emit event
            events.candidate.removed_from_pool.send(
                sender=self.__class__,
                talent_pool=talent_pool,
                candidate=candidate,
                user=request.user,
                request=request
            )
            
        return success_response(
            data={'removed_count': removed_count},
            message=f"{removed_count} candidates removed from pool."
        )

class TalentPoolMembershipViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CandidateTalentPoolMembershipSerializer
    queryset = CandidateTalentPoolMembership.objects.all()

    def get_queryset(self):
        qs = self.queryset.filter(tenant_id=self.request.user.tenant_id)
        pool_id = self.request.query_params.get('talent_pool_id')
        if pool_id:
            qs = qs.filter(talent_pool_id=pool_id)
        candidate_id = self.request.query_params.get('candidate_id')
        if candidate_id:
            qs = qs.filter(candidate_id=candidate_id)
        return qs

    def perform_create(self, serializer):
        membership = serializer.save(
            tenant_id=self.request.user.tenant_id,
            added_by=self.request.user.id
        )
        # Emit event
        events.candidate.added_to_pool.send(
            sender=self.__class__,
            membership=membership,
            user=self.request.user,
            request=self.request
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Capture data for event before delete
        membership_id = instance.id
        talent_pool = instance.talent_pool
        candidate = instance.candidate
        
        self.perform_destroy(instance)
        
        # Emit event
        events.candidate.removed_from_pool.send(
            sender=self.__class__,
            talent_pool=talent_pool,
            candidate=candidate,
            user=request.user,
            request=request
        )
        
        return success_response(message="Candidate removed from pool.")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data={'memberships': serializer.data},
            message="Memberships retrieved."
        )
