from django.db.models import Count
from django.db import transaction
from django.utils.text import slugify
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.core.responses import success_response, error_response
from apps.core import events
from apps.candidates.models import Candidate
from .models import TalentPool, CandidateTalentPoolMembership
from .serializers import (
    TalentPoolSerializer, 
    CandidateTalentPoolMembershipSerializer,
    BulkAddCandidateSerializer,
    TalentPoolActivitySerializer,
)
from .services import record_talent_pool_activity

class TalentPoolViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TalentPoolSerializer
    queryset = TalentPool.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = self.queryset.filter(
            tenant_id=self.request.user.tenant_id,
        )
        if self.action == 'list':
            qs = qs.filter(is_active=True)
        return qs.annotate(member_count=Count('memberships'))

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
        record_talent_pool_activity(
            talent_pool=instance,
            event_type='talent_pool.created',
            actor=self.request.user,
            source='manual',
            payload={
                'method': 'manual',
                'pool_name': instance.name,
                'tenant_type': instance.tenant_type,
                'context_label': instance.name,
            }
        )

    def perform_update(self, serializer):
        previous = self.get_object()
        previous_state = {
            'name': previous.name,
            'description': previous.description,
            'color': previous.color,
            'pool_type': previous.pool_type,
            'is_active': previous.is_active,
        }
        instance = serializer.save()

        changed_fields = [
            field for field, previous_value in previous_state.items()
            if getattr(instance, field) != previous_value
        ]
        if not changed_fields:
            return

        if previous_state['is_active'] and not instance.is_active:
            events.talent_pool.archived.send(
                sender=self.__class__,
                talent_pool=instance,
                user=self.request.user,
                request=self.request
            )
            record_talent_pool_activity(
                talent_pool=instance,
                event_type='talent_pool.archived',
                actor=self.request.user,
                source='manual',
                payload={
                    'method': 'manual',
                    'pool_name': instance.name,
                    'changed_fields': changed_fields,
                    'context_label': instance.name,
                }
            )
            return

        events.talent_pool.updated.send(
            sender=self.__class__,
            talent_pool=instance,
            user=self.request.user,
            request=self.request
        )
        record_talent_pool_activity(
            talent_pool=instance,
            event_type='talent_pool.updated',
            actor=self.request.user,
            source='manual',
            payload={
                'method': 'manual',
                'pool_name': instance.name,
                'changed_fields': changed_fields,
                'context_label': instance.name,
            }
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

    @action(detail=True, methods=['get'], url_path='activity')
    def activity(self, request, pk=None):
        talent_pool = self.get_object()
        qs = talent_pool.activity_events.filter(
            tenant_id=request.user.tenant_id
        ).select_related('actor')[:100]
        serializer = TalentPoolActivitySerializer(qs, many=True)
        return success_response(
            data={'activity': serializer.data},
            message="Talent pool activity retrieved."
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

        normalized_candidate_ids = [str(candidate_id) for candidate_id in candidate_ids]
        duplicate_request_ids = sorted({
            candidate_id for candidate_id in normalized_candidate_ids
            if normalized_candidate_ids.count(candidate_id) > 1
        })
        if duplicate_request_ids:
            return error_response(
                "Duplicate candidates were selected.",
                {'candidate_ids': ['Each candidate can only be selected once per request.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        valid_candidate_ids = set(
            str(candidate_id) for candidate_id in Candidate.objects.filter(
                id__in=candidate_ids,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            ).values_list('id', flat=True)
        )
        missing_candidate_ids = sorted(
            candidate_id for candidate_id in normalized_candidate_ids
            if candidate_id not in valid_candidate_ids
        )
        if missing_candidate_ids:
            return error_response(
                "One or more selected candidates are unavailable in this tenant.",
                {'candidate_ids': ['Some candidates could not be found for this workspace.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        existing_membership_ids = set(
            str(candidate_id) for candidate_id in CandidateTalentPoolMembership.objects.filter(
                talent_pool=talent_pool,
                candidate_id__in=candidate_ids,
                tenant_id=request.user.tenant_id
            ).values_list('candidate_id', flat=True)
        )
        if existing_membership_ids:
            return error_response(
                "Some selected candidates are already members of this pool.",
                {'candidate_ids': ['Remove existing members from the selection and try again.']},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        added_count = 0
        with transaction.atomic():
            for candidate_id in candidate_ids:
                membership = CandidateTalentPoolMembership.objects.create(
                    talent_pool=talent_pool,
                    candidate_id=candidate_id,
                    tenant_id=request.user.tenant_id,
                    added_by=request.user.id,
                    note=note,
                    source=source
                )
                added_count += 1
                # Emit event
                events.candidate.added_to_pool.send(
                    sender=self.__class__,
                    membership=membership,
                    user=request.user,
                    request=request
                )
                record_talent_pool_activity(
                    talent_pool=talent_pool,
                    event_type='candidate.added_to_pool',
                    actor=request.user,
                    source=source,
                    payload={
                        'method': source,
                        'pool_name': talent_pool.name,
                        'candidate_id': str(membership.candidate_id),
                        'candidate_name': str(membership.candidate),
                        'context_label': talent_pool.name,
                    }
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
            record_talent_pool_activity(
                talent_pool=talent_pool,
                event_type='candidate.removed_from_pool',
                actor=request.user,
                source='manual',
                payload={
                    'method': 'manual',
                    'pool_name': talent_pool.name,
                    'candidate_id': str(candidate.id),
                    'candidate_name': str(candidate),
                    'context_label': talent_pool.name,
                }
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
        record_talent_pool_activity(
            talent_pool=membership.talent_pool,
            event_type='candidate.added_to_pool',
            actor=self.request.user,
            source=membership.source,
            payload={
                'method': membership.source,
                'pool_name': membership.talent_pool.name,
                'candidate_id': str(membership.candidate_id),
                'candidate_name': str(membership.candidate),
                'context_label': membership.talent_pool.name,
            }
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
        record_talent_pool_activity(
            talent_pool=talent_pool,
            event_type='candidate.removed_from_pool',
            actor=request.user,
            source='manual',
            payload={
                'method': 'manual',
                'pool_name': talent_pool.name,
                'candidate_id': str(candidate.id),
                'candidate_name': str(candidate),
                'context_label': talent_pool.name,
            }
        )
        
        return success_response(message="Candidate removed from pool.")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data={'memberships': serializer.data},
            message="Memberships retrieved."
        )
