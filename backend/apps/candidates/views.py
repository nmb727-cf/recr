from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import uuid

from apps.candidates.models import (
    Candidate,
    CandidateProfile,
    CandidateNote,
    CandidateTenantRight,
    CandidateWorkspace,
    CandidateEngagement,
    CandidateTimelineEvent,
    CandidateWorkflowPolicy,
    GENERAL_CANDIDATE_STAGES,
    JOB_CANDIDATE_STAGES,
)
from apps.candidates.serializers import (
    CandidateSerializer, CandidateDetailSerializer,
    CandidateProfileSerializer, CandidateNoteSerializer,
    CandidateWorkspaceSerializer,
    CandidateEngagementSerializer,
    CandidateTimelineEventSerializer,
    CandidateWorkflowPolicySerializer,
)
from apps.candidates.protection import (
    check_protected_action,
    find_duplicate_protected_candidate,
    protection_badge_payload,
)
from apps.core.responses import success_response, error_response
from apps.rbac.permissions import require_permission
from apps.organisations.models import TeamMembership
from apps.accounts.models import CustomUser
from apps.pipeline.models import Application


SYSTEM_DEFAULT_WORKFLOW_MODE = 'manual'
ACTIVE_WORK_STAGES = [
    'new_lead',
    'contacted',
    'follow_up',
    'qualified',
    'nurture',
    'dormant',
]
POST_ADD_NEXT_ACTIONS = [
    'save_to_database_only',
    'add_to_active_work',
    'match_to_jobs',
    'send_info_request_link',
    'assign_to_recruiter',
    'keep_in_nurture_pool',
]


def _resolve_workflow_mode(user, candidate=None, job=None):
    if job and job.override_workflow_mode:
        return job.override_workflow_mode

    team_ids = TeamMembership.objects.filter(
        tenant_id=user.tenant_id,
        user_id=user.id
    ).values_list('team_id', flat=True)

    recruiter_policy = CandidateWorkflowPolicy.objects.filter(
        tenant_id=user.tenant_id,
        recruiter_user_id=user.id,
        is_active=True
    ).first()
    if recruiter_policy:
        return recruiter_policy.default_candidate_workflow_mode

    team_policy = CandidateWorkflowPolicy.objects.filter(
        tenant_id=user.tenant_id,
        team_id__in=team_ids,
        recruiter_user_id__isnull=True,
        is_active=True
    ).order_by('-updated_at').first()
    if team_policy:
        return team_policy.default_candidate_workflow_mode

    tenant_policy = CandidateWorkflowPolicy.objects.filter(
        tenant_id=user.tenant_id,
        team_id__isnull=True,
        recruiter_user_id__isnull=True,
        is_active=True
    ).first()
    if tenant_policy:
        return tenant_policy.default_candidate_workflow_mode

    if candidate and candidate.workflow_mode:
        return candidate.workflow_mode
    return SYSTEM_DEFAULT_WORKFLOW_MODE


def _workflow_behavior(mode):
    if mode == 'fully_automated':
        return {
            'mode': mode,
            'auto_actions_enabled': True,
            'suggestions_enabled': True,
            'user_approval_required': False,
        }
    if mode == 'semi_automated':
        return {
            'mode': mode,
            'auto_actions_enabled': False,
            'suggestions_enabled': True,
            'user_approval_required': True,
        }
    return {
        'mode': 'manual',
        'auto_actions_enabled': False,
        'suggestions_enabled': False,
        'user_approval_required': True,
    }


def _extract_stage_note(payload):
    note = (
        payload.get('note')
        or payload.get('notes')
        or payload.get('reason')
        or payload.get('stage_change_note')
        or ''
    )
    return str(note).strip()


def _require_stage_note(payload):
    note = _extract_stage_note(payload)
    if not note:
        return None, error_response(
            "A mandatory note/reason is required for every stage change.",
            {'note': ['This field is required.']}
        )
    return note, None


def _candidate_warning_signals(candidate):
    warnings = []
    if not candidate.email and not candidate.phone and not candidate.phone_number:
        warnings.append('missing_contact_info')
    if candidate.is_duplicate or candidate.duplicate_of:
        warnings.append('duplicate')
    if candidate.next_follow_up_at and candidate.next_follow_up_at < timezone.now():
        warnings.append('follow_up_overdue')
    if candidate.profile_completeness < 60:
        warnings.append('incomplete_profile')
    return warnings


def _candidate_smart_row(candidate, job_summary=None, owner_name_map=None, tenant_id=None):
    owner_name = None
    owner_id = str(candidate.owner_user_id) if candidate.owner_user_id else None
    if owner_name_map and owner_id:
        owner_name = owner_name_map.get(owner_id)
    open_engagements = sum(job_summary.values()) if job_summary else 0
    payload = {
        'id': str(candidate.id),
        'name': candidate.full_name,
        'current_title': candidate.current_title,
        'company': candidate.current_company,
        'experience': float(candidate.experience_years) if candidate.experience_years is not None else None,
        'location': ", ".join(
            [x for x in [candidate.current_location_city, candidate.current_location_country] if x]
        ),
        'source': candidate.source or candidate.source_type,
        'source_type': candidate.source_type or '',
        'engagement_stage': candidate.engagement_stage,
        'owner': str(candidate.owner_user_id) if candidate.owner_user_id else None,
        'owner_name': owner_name,
        'last_touch': candidate.last_contact_at,
        'last_activity': candidate.last_activity_at or candidate.updated_at,
        'signals': {
            'readiness_score': candidate.readiness_score,
            'fit_score': candidate.fit_score,
            'warning_signals': _candidate_warning_signals(candidate),
        },
        'job_engagement_summary': job_summary or {},
        'skills': (candidate.skills or [])[:6],
        'passport_linked': candidate.passport_linked or bool(candidate.passport_id),
        'is_duplicate': candidate.is_duplicate or bool(getattr(candidate, 'duplicate_of', None)),
        'notice_period_days': candidate.notice_period_days,
        'availability_status': candidate.availability_status,
        'open_engagements': open_engagements,
    }
    if tenant_id:
        payload.update(protection_badge_payload(candidate_id=candidate.id, target_tenant_id=tenant_id))
    return payload


def _structured_activity_item(event):
    payload = event.payload or {}
    context_type = 'general'
    if event.engagement and event.engagement.job_id:
        context_type = 'job'
    if payload.get('context_type') in ['job', 'general']:
        context_type = payload.get('context_type')

    method = payload.get('method')
    if not method:
        if event.source == 'system':
            method = 'system'
        elif payload.get('method_hint'):
            method = payload.get('method_hint')
        else:
            method = 'manual'

    return {
        'candidate_id': str(event.candidate_id),
        'engagement_id': str(event.engagement_id) if event.engagement_id else None,
        'actor_id': str(event.actor_id) if event.actor_id else None,
        'actor_type': 'system' if event.actor_id is None else 'user',
        'action_type': event.event_type,
        'context_type': context_type,
        'method': method,
        'metadata_json': payload,
        'created_at': event.created_at,
        'actor': f"{event.actor.first_name} {event.actor.last_name}".strip() if event.actor else 'System',
    }


def _structured_note_item(note):
    context_type = 'general'
    if note.engagement_id:
        context_type = 'job' if note.engagement and note.engagement.job_id else 'general'
    elif note.note_context and note.note_context != 'general':
        context_type = 'job'

    return {
        'candidate_id': str(note.candidate_id),
        'engagement_id': str(note.engagement_id) if note.engagement_id else None,
        'author_id': str(note.created_by) if note.created_by else None,
        'author': str(note.created_by) if note.created_by else 'System',
        'note_type': note.note_type,
        'content': note.note_text,
        'context_type': context_type,
        'created_at': note.created_at,
    }


def _apply_saved_view(qs, view_name, stale_days=21):
    now = timezone.now()
    if view_name == 'active_work':
        return qs.filter(is_in_active_work=True)
    if view_name == 'recently_added':
        return qs.filter(created_at__gte=now - timedelta(days=14))
    if view_name == 'passport_linked':
        return qs.filter(Q(passport_linked=True) | Q(passport_id__isnull=False))
    if view_name == 'agency_submitted':
        return qs.filter(Q(source='agency') | Q(source_type='agency'))
    if view_name == 'duplicates':
        return qs.filter(
            Q(is_duplicate=True) | Q(duplicate_of__isnull=False) |
            Q(duplicate_review_status__in=['pending_review', 'confirmed_duplicate'])
        )
    if view_name == 'dormant':
        return qs.filter(last_activity_at__lt=now - timedelta(days=stale_days))
    if view_name == 'general_pool':
        return qs.filter(candidate_pool='GENERAL', active_job_id__isnull=True)
    if view_name == 'follow_up_due':
        return qs.filter(next_follow_up_at__isnull=False, next_follow_up_at__lte=now)
    if view_name == 'ready_to_submit':
        return qs.filter(
            engagement_stage__in=['qualified'],
            readiness_score__gte=70
        )
    if view_name == 'missing_contact_info':
        return qs.filter(
            Q(email='') |
            (Q(phone='') & Q(phone_number=''))
        )
    return qs


class CandidateListView(APIView):
    permission_classes = [IsAuthenticated, require_permission('candidates.candidate.view')]

    def get(self, request):
        # Candidates visible to this tenant:
        # 1. Candidates they created (tenant_id = their tenant)
        # 2. Self-registered candidates (tenant_id = null) — only if they have an application
        qs = Candidate.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        # Search
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(current_title__icontains=search) |
                Q(current_company__icontains=search)
            )

        # Filter by skills
        skills = request.query_params.get('skills')
        if skills:
            qs = qs.filter(skills__contains=[skills])

        # Filter by experience
        exp_min = request.query_params.get('experience_min')
        if exp_min:
            qs = qs.filter(experience_years__gte=exp_min)

        # Filter by source
        source = request.query_params.get('source')
        if source:
            qs = qs.filter(source=source)

        # Filter actively looking
        actively_looking = request.query_params.get('actively_looking')
        if actively_looking:
            qs = qs.filter(is_actively_looking=actively_looking.lower() == 'true')

        return success_response(
            data={'candidates': CandidateSerializer(qs, many=True).data},
            message="Candidates retrieved.",
            meta={'total': qs.count()}
        )

    def post(self, request):
        from apps.rbac.utils import user_has_permission
        if not user_has_permission(request.user, 'candidates.candidate.create'):
            return error_response(
                "You do not have permission to create candidates.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Deduplication check
        email = request.data.get('email', '').strip().lower()
        phone = request.data.get('phone', '').strip()
        passport_id = request.data.get('passport_id')
        global_hash = request.data.get('global_hash', '').strip()

        protected_candidate, protected_right = find_duplicate_protected_candidate(
            tenant_id=request.user.tenant_id,
            email=email,
            phone=phone,
            passport_id=passport_id,
            global_hash=global_hash,
        )
        if protected_candidate and protected_right:
            _, message, _ = check_protected_action(
                candidate_id=protected_candidate.id,
                tenant_id=request.user.tenant_id,
                action='manual_import_candidate',
                actor_user_id=request.user.id,
            )
            return error_response(
                message or "Candidate is protected under agency agreement.",
                errors={
                    'candidate_id': str(protected_candidate.id),
                    'is_agency_protected': True,
                    'protection_scope': protected_right.retention_scope,
                    'protected_until': protected_right.protected_until,
                },
                status_code=status.HTTP_409_CONFLICT,
            )

        existing = None
        if email:
            existing = Candidate.objects.filter(
                email__iexact=email,
                is_deleted=False
            ).first()
        if not existing and phone:
            existing = Candidate.objects.filter(
                phone=phone,
                is_deleted=False
            ).first()

        if existing:
            return Response({
                'success': False,
                'duplicate': True,
                'message': 'A candidate already exists with this email or phone.',
                'existing_candidate': {
                    'id': str(existing.id),
                    'name': f'{existing.first_name} {existing.last_name}',
                    'email': existing.email,
                    'phone': existing.phone,
                    'current_title': existing.current_title,
                }
            }, status=status.HTTP_409_CONFLICT)

        payload = request.data.copy()
        entry_type = payload.pop('entry_type', payload.pop('entry_method', 'manual'))
        send_invite = payload.pop('send_invite', False)
        next_action = payload.pop('next_action', 'save_to_database_only')
        if next_action not in POST_ADD_NEXT_ACTIONS:
            next_action = 'save_to_database_only'

        serializer = CandidateSerializer(data=payload)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        candidate = serializer.save(
            tenant_id=request.user.tenant_id,
            owner_user_id=request.user.id,
            owner_tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            workflow_mode=_resolve_workflow_mode(request.user),
            source_type=payload.get('source_type') or 'direct',
            last_activity_at=timezone.now(),
            candidate_state='NEW_LEAD',
            candidate_pool='GENERAL',
            is_general_pool_used=False,
        )

        # Auto-create empty profile
        CandidateProfile.objects.create(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate.id,
            created_by=request.user.id,
        )

        if entry_type in ['invite', 'quick_add', 'invite_candidate']:
            import secrets
            candidate.profile_status = 'draft'
            candidate.initial_entry_type = 'invite'
            candidate.claim_token = secrets.token_urlsafe(32)
            candidate.claim_token_expires_at = (
                timezone.now() + timedelta(days=30)
            )
        else:
            candidate.profile_status = 'partial'
            candidate.initial_entry_type = entry_type if entry_type else 'manual'

        send_invite_bool = send_invite
        if isinstance(send_invite, str):
            send_invite_bool = send_invite.lower() in ['1', 'true', 'yes', 'on']

        if send_invite_bool and candidate.claim_token:
            candidate.account_status = 'invited'
            candidate.invite_sent_at = timezone.now()
            # ── Source 1: Notify candidate that their profile was added ────
            # The claim link carries the candidate's identity context (email +
            # phone) prefilled from this record.  When the candidate follows
            # the link they are taken to /candidate/claim/<token> where:
            #   • If no user account exists  → signup form (email/phone prefilled)
            #   • If a user account exists   → login screen
            # On successful auth the backend links the user to this candidate
            # record and marks account_status = 'claimed'.
            #
            # TODO (Phase 2): Replace print stub with actual email/SMS/WhatsApp
            # delivery via the communications service.
            claim_url = f"/candidate/claim/{candidate.claim_token}"
            print(
                f"[NOTIFICATION STUB] Source 1 — candidate profile added.\n"
                f"  To: {candidate.email or candidate.phone}\n"
                f"  Claim link: {claim_url}\n"
                f"  Message: 'Your profile has been added. "
                f"Click the link to view and claim your profile.'"
            )

        candidate.save()

        # Auto-create engagement as the default Active Work card surface.
        created_engagement = None
        try:
            # Check for existing active general engagement (precaution)
            created_engagement = CandidateEngagement.objects.filter(
                tenant_id=request.user.tenant_id,
                candidate=candidate,
                job__isnull=True,
                is_active=True,
                is_deleted=False
            ).first()
            
            if not created_engagement:
                created_engagement = CandidateEngagement.objects.create(
                    tenant_id=request.user.tenant_id,
                    candidate=candidate,
                    engagement_type='sourced',
                    stage='new_lead',
                    priority='warm',
                    is_active=True,
                    owner_user=request.user,
                    created_by=request.user,
                    last_activity_at=timezone.now(),
                    metadata={'auto_created': True, 'source': 'candidate_database'}
                )
        except Exception as e:
            print(f"Failed to auto-create engagement: {e}")

        if next_action == 'save_to_database_only':
            candidate.is_in_active_work = False
            if created_engagement:
                created_engagement.is_active = False
                created_engagement.save(update_fields=['is_active', 'updated_at'])
        elif next_action == 'add_to_active_work':
            candidate.is_in_active_work = True
            candidate.lifecycle_state = 'active'
            candidate.engagement_stage = 'new_lead'
            if created_engagement:
                created_engagement.is_active = True
                created_engagement.stage = 'new_lead'
                created_engagement.save()
        elif next_action == 'match_to_jobs':
            candidate.lifecycle_state = 'active'
            candidate.is_in_active_work = True
            # This logic usually leads to job engagement creation via modal
        elif next_action == 'send_info_request_link':
            if not candidate.claim_token:
                import secrets
                candidate.claim_token = secrets.token_urlsafe(32)
                candidate.claim_token_expires_at = timezone.now() + timedelta(days=30)
            candidate.account_status = 'invited'
            candidate.invite_sent_at = timezone.now()
        elif next_action == 'assign_to_recruiter':
            assignee = request.data.get('assign_user_id')
            if assignee:
                candidate.owner_user_id = assignee
            candidate.is_in_active_work = True
            candidate.lifecycle_state = 'active'
            if created_engagement:
                created_engagement.is_active = True
                if assignee:
                    created_engagement.owner_user_id = assignee
                created_engagement.save()
        elif next_action == 'keep_in_nurture_pool':
            candidate.lifecycle_state = 'nurture'
            candidate.engagement_stage = 'nurture'
            candidate.auto_nurture_enabled = True
            candidate.is_in_active_work = False
            if created_engagement:
                created_engagement.is_active = True
                created_engagement.stage = 'nurture'
                created_engagement.save()

        candidate.save()

        response_data = {
            'candidate': CandidateSerializer(candidate).data,
            'next_step_selected': next_action,
            'next_step_options': POST_ADD_NEXT_ACTIONS,
            'workflow_behavior': _workflow_behavior(candidate.workflow_mode),
        }
        if candidate.claim_token:
            response_data['claim_token'] = candidate.claim_token
            # Use /candidate/claim/ path — matches the frontend route and
            # the CandidateClaimVerifyView backend endpoint.
            response_data['claim_link'] = (
                f"/candidate/claim/{candidate.claim_token}"
            )

        return success_response(
            data=response_data,
            message="Candidate created.",
            status_code=status.HTTP_201_CREATED
        )


from apps.talent_pools.models import TalentPool, CandidateTalentPoolMembership
from apps.talent_pools.serializers import TalentPoolSerializer

class CandidateTalentPoolsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            candidate = Candidate.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Candidate.DoesNotExist:
            return error_response("Candidate not found.", status_code=status.HTTP_404_NOT_FOUND)

        memberships = CandidateTalentPoolMembership.objects.filter(
            candidate=candidate,
            tenant_id=request.user.tenant_id
        ).select_related('talent_pool')
        
        pools = [m.talent_pool for m in memberships]
        serializer = TalentPoolSerializer(pools, many=True)
        
        return success_response(
            data={'talent_pools': serializer.data},
            message="Candidate talent pools retrieved."
        )

class CandidateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return Candidate.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Candidate.DoesNotExist:
            return None

    def get(self, request, pk):
        candidate = self.get_object(request, pk)
        if not candidate:
            return error_response("Candidate not found.", status_code=status.HTTP_404_NOT_FOUND)
        candidate_payload = CandidateDetailSerializer(candidate).data
        candidate_payload.update(
            protection_badge_payload(candidate_id=candidate.id, target_tenant_id=request.user.tenant_id)
        )

        return success_response(
            data={'candidate': candidate_payload},
            message="Candidate retrieved."
        )

    def put(self, request, pk):
        candidate = self.get_object(request, pk)
        if not candidate:
            return error_response("Candidate not found.", status_code=status.HTTP_404_NOT_FOUND)

        old_candidate_stage = candidate.engagement_stage
        if 'engagement_stage' in request.data and request.data.get('engagement_stage') != old_candidate_stage:
            stage_note, note_error = _require_stage_note(request.data)
            if note_error:
                return note_error
        else:
            stage_note = None

        serializer = CandidateSerializer(candidate, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        updated_candidate = serializer.save()
        if stage_note:
            CandidateTimelineEvent.objects.create(
                tenant_id=request.user.tenant_id,
                candidate_id=updated_candidate.id,
                event_type='candidate.stage_changed',
                actor=request.user,
                payload={
                    'from_stage': old_candidate_stage,
                    'to_stage': updated_candidate.engagement_stage,
                    'note': stage_note,
                    'changed_by': str(request.user.id),
                    'changed_at': timezone.now().isoformat(),
                },
                source='user'
            )
        return success_response(
            data={'candidate': serializer.data},
            message="Candidate updated."
        )

    def delete(self, request, pk):
        candidate = self.get_object(request, pk)
        if not candidate:
            return error_response("Candidate not found.", status_code=status.HTTP_404_NOT_FOUND)

        candidate.soft_delete()
        return success_response(
            message="Candidate deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )


class CandidateTimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            Candidate.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Candidate.DoesNotExist:
            return error_response("Candidate not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Get notes as timeline events
        notes = CandidateNote.objects.filter(
            candidate_id=pk,
            is_deleted=False
        ).order_by('-created_at')

        events = []
        for note in notes:
            events.append({
                'type': 'note',
                'note_type': note.note_type,
                'text': note.note_text,
                'created_at': note.created_at,
                'created_by': note.created_by,
            })

        return success_response(
            data={'events': events},
            message="Timeline retrieved."
        )


class CandidateDuplicatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Find candidates with same global_hash within tenant
        from django.db.models import Count
        duplicates = Candidate.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
            is_duplicate=False
        ).exclude(global_hash='').values('global_hash').annotate(
            count=Count('id')
        ).filter(count__gt=1)

        duplicate_groups = []
        for dup in duplicates:
            candidates = Candidate.objects.filter(
                global_hash=dup['global_hash'],
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
            duplicate_groups.append(
                CandidateSerializer(candidates, many=True).data
            )

        return success_response(
            data={'duplicate_groups': duplicate_groups},
            message="Duplicates retrieved."
        )


class CandidateMergeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        primary_id = request.data.get('primary_id')
        duplicate_ids = request.data.get('duplicate_ids', [])

        if not primary_id or not duplicate_ids:
            return error_response("primary_id and duplicate_ids are required.")

        try:
            primary = Candidate.objects.get(
                id=primary_id,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Candidate.DoesNotExist:
            return error_response("Primary candidate not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Mark duplicates
        Candidate.objects.filter(
            id__in=duplicate_ids,
            tenant_id=request.user.tenant_id
        ).update(is_duplicate=True, duplicate_of=primary_id)

        return success_response(
            data={'candidate': CandidateSerializer(primary).data},
            message=f"Merged {len(duplicate_ids)} duplicate(s) into primary candidate."
        )


class CandidateNoteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Verify candidate belongs to tenant
        try:
            Candidate.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Candidate.DoesNotExist:
            return error_response("Candidate not found.", status_code=status.HTTP_404_NOT_FOUND)

        notes = CandidateNote.objects.filter(
            candidate_id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        # Hide private notes from non-owners
        if not request.query_params.get('include_private'):
            notes = notes.filter(
                Q(is_private=False) | Q(created_by=request.user.id)
            )

        return success_response(
            data={'notes': CandidateNoteSerializer(notes, many=True).data},
            message="Notes retrieved."
        )

    def post(self, request, pk):
        try:
            Candidate.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Candidate.DoesNotExist:
            return error_response("Candidate not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = CandidateNoteSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save(
            tenant_id=request.user.tenant_id,
            candidate_id=pk,
            created_by=request.user.id,
        )
        return success_response(
            data={'note': serializer.data},
            message="Note created.",
            status_code=status.HTTP_201_CREATED
        )


class CandidateNoteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk, note_id):
        try:
            return CandidateNote.objects.get(
                id=note_id,
                candidate_id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except CandidateNote.DoesNotExist:
            return None

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Note updated"),
            404: OpenApiResponse(description="Note not found"),
        }
    )
    def put(self, request, pk, note_id):
        note = self.get_object(request, pk, note_id)
        if not note:
            return error_response("Note not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Only note creator can edit
        if note.created_by != request.user.id:
            return error_response(
                "You can only edit your own notes.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = CandidateNoteSerializer(note, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'note': serializer.data},
            message="Note updated."
        )

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Note deleted"),
            404: OpenApiResponse(description="Note not found"),
        }
    )
    def delete(self, request, pk, note_id):
        note = self.get_object(request, pk, note_id)
        if not note:
            return error_response("Note not found.", status_code=status.HTTP_404_NOT_FOUND)

        if note.created_by != request.user.id:
            return error_response(
                "You can only delete your own notes.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        note.soft_delete()
        return success_response(
            message="Note deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )


class SkillSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.candidates.models import Skill
        q = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 20))

        if q:
            skills = Skill.objects.filter(
                name__icontains=q,
                is_active=True
            ).order_by('-usage_count', 'name')[:limit]
        else:
            skills = Skill.objects.filter(
                is_active=True
            ).order_by('-usage_count')[:limit]

        return success_response(
            data={
                'skills': [
                    {
                        'id': str(s.id),
                        'name': s.name,
                        'category': s.category
                    }
                    for s in skills
                ]
            },
            message="Skills retrieved."
        )


GLOBAL_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai',
    'Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Surat',
    'New York', 'San Francisco', 'Los Angeles', 'Chicago',
    'Seattle', 'Austin', 'Boston', 'Miami', 'Denver',
    'London', 'Manchester', 'Birmingham', 'Edinburgh',
    'Dubai', 'Abu Dhabi', 'Singapore', 'Sydney', 'Melbourne',
    'Toronto', 'Vancouver', 'Berlin', 'Amsterdam', 'Paris',
    'Remote', 'Hybrid', 'Open to Relocation',
]


class LocationSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.organisations.models import Location
        q = request.query_params.get('q', '').strip().lower()

        results = []

        # Tenant office locations first
        tenant_locations = Location.objects.filter(
            tenant_id=request.user.tenant_id,
            is_active=True,
            is_deleted=False
        )
        if q:
            tenant_locations = tenant_locations.filter(
                name__icontains=q
            ) | tenant_locations.filter(
                city__icontains=q
            )
        for loc in tenant_locations[:5]:
            label = loc.city or loc.name
            if label and label not in results:
                results.append(label)

        # Global cities
        for city in GLOBAL_CITIES:
            if not q or q in city.lower():
                if city not in results:
                    results.append(city)
            if len(results) >= 20:
                break

        return success_response(
            data={'locations': results},
            message="Locations retrieved."
        )

class CandidateWorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, candidate_id):
        try:
            workspace = CandidateWorkspace.objects.get(
                candidate_id=candidate_id,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
            serializer = CandidateWorkspaceSerializer(workspace)
            return success_response(serializer.data)
        except CandidateWorkspace.DoesNotExist:
            return error_response("Workspace not found", status_code=404)

    def put(self, request, candidate_id):
        workspace, created = CandidateWorkspace.objects.get_or_create(
            candidate_id=candidate_id,
            tenant_id=request.user.tenant_id,
            defaults={'created_by': request.user}
        )
        serializer = CandidateWorkspaceSerializer(
            workspace, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save(updated_at=timezone.now())
            return success_response(serializer.data)
        return error_response(serializer.errors)


class CandidateEngagementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, candidate_id):
        # active=true returns only active engagements
        # active=false returns only closed/historical
        # no param returns all
        active_param = request.query_params.get('active', None)
        qs = CandidateEngagement.objects.filter(
            candidate_id=candidate_id,
            tenant_id=request.user.tenant_id,
            is_deleted=False
        ).order_by('-started_at')

        if active_param == 'true':
            qs = qs.filter(is_active=True)
        elif active_param == 'false':
            qs = qs.filter(is_active=False)

        serializer = CandidateEngagementSerializer(qs, many=True)
        return success_response(serializer.data)

    def post(self, request, candidate_id):
        data = request.data.copy()
        data['candidate'] = candidate_id
        job_id = data.get('job')
        if job_id:
            allowed, message, _ = check_protected_action(
                candidate_id=candidate_id,
                tenant_id=request.user.tenant_id,
                action='workflow_allowed_job',
                job_id=job_id,
                actor_user_id=request.user.id,
            )
            if not allowed:
                return error_response(message, status_code=status.HTTP_403_FORBIDDEN)
        
        if not data.get('stage'):
            data['stage'] = 'submitted' if job_id else 'new_lead'

        # Enforce: one active presence maximum per candidate per job (or general).
        if job_id:
            existing_job_eng = CandidateEngagement.objects.filter(
                candidate_id=candidate_id,
                tenant_id=request.user.tenant_id,
                job_id=job_id,
                is_active=True,
                is_deleted=False,
            ).order_by('-started_at').first()
            if existing_job_eng:
                return error_response(
                    message="Candidate already has an active engagement for this job.",
                    status_code=status.HTTP_409_CONFLICT
                )
        else:
            existing_general = CandidateEngagement.objects.filter(
                candidate_id=candidate_id,
                tenant_id=request.user.tenant_id,
                job__isnull=True,
                is_active=True,
                is_deleted=False,
            ).order_by('-started_at').first()
            if existing_general:
                old_stage = existing_general.stage
                new_stage = data.get('stage', old_stage)
                
                # If stage is same, return conflict to prevent misleading "Updated" notification
                if old_stage == new_stage:
                    return error_response(
                        message="Candidate is already in the active general pool.",
                        status_code=status.HTTP_409_CONFLICT
                    )
                
                existing_general.stage = new_stage
                existing_general.last_activity_at = timezone.now()
                existing_general.save()
                
                # Sync candidate stage
                Candidate.objects.filter(id=candidate_id).update(
                    engagement_stage=new_stage,
                    last_activity_at=timezone.now()
                )
                
                if old_stage != new_stage:
                    from apps.candidates.signals import emit_timeline_event
                    emit_timeline_event(
                        tenant_id=request.user.tenant_id,
                        candidate_id=candidate_id,
                        engagement=existing_general,
                        event_type='engagement.stage_changed',
                        actor=request.user,
                        payload={
                            'from_stage': old_stage,
                            'to_stage': new_stage,
                            'note': 'General track stage updated via enforcement'
                        },
                        source='user'
                    )
                    
                return success_response(
                    data=CandidateEngagementSerializer(existing_general).data,
                    message="Updated existing general presence."
                )

        # If owner_user is "me" or missing, set to current user
        owner_user = data.get('owner_user')
        if not owner_user or owner_user == 'me':
            data['owner_user'] = str(request.user.id)

        serializer = CandidateEngagementSerializer(data=data)
        if serializer.is_valid():
            engagement = serializer.save(
                tenant_id=request.user.tenant_id,
                created_by=request.user,
                owner_user=request.user if not owner_user or owner_user == 'me' else serializer.validated_data.get('owner_user'),
                last_activity_at=timezone.now()
            )
            candidate_updates = {'last_activity_at': timezone.now()}
            if engagement.job_id is None:
                candidate_updates['is_in_active_work'] = True
                candidate_updates['engagement_stage'] = engagement.stage
            else:
                from apps.candidates.signals import transition_candidate_to_job_track
                transition_candidate_to_job_track(
                    candidate_id=candidate_id,
                    tenant_id=request.user.tenant_id,
                    job_id=engagement.job_id,
                )
                candidate_updates['is_in_active_work'] = False
                candidate_updates['active_job_id'] = engagement.job_id
            Candidate.objects.filter(id=candidate_id).update(**candidate_updates)
            # Emit timeline event
            CandidateTimelineEvent.objects.create(
                tenant_id=request.user.tenant_id,
                candidate_id=candidate_id,
                engagement=engagement,
                event_type='engagement.opened',
                actor=request.user,
                payload={
                    'engagement_type': engagement.engagement_type,
                    'stage': engagement.stage,
                    'priority': engagement.priority,
                    'job_id': str(engagement.job_id) if engagement.job_id else None
                },
                source='user'
            )
            return success_response(
                CandidateEngagementSerializer(engagement).data,
                status_code=201
            )
        return error_response(serializer.errors)


class CandidateEngagementDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, candidate_id, engagement_id, tenant_id):
        try:
            return CandidateEngagement.objects.get(
                id=engagement_id,
                candidate_id=candidate_id,
                tenant_id=tenant_id,
                is_deleted=False
            )
        except CandidateEngagement.DoesNotExist:
            return None

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Engagement retrieved"),
            404: OpenApiResponse(description="Engagement not found"),
        }
    )
    def get(self, request, candidate_id, engagement_id):
        engagement = self.get_object(
            candidate_id, engagement_id, request.user.tenant_id
        )
        if not engagement:
            return error_response("Engagement not found", status_code=404)
        serializer = CandidateEngagementSerializer(engagement)
        return success_response(serializer.data)

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Engagement updated"),
            404: OpenApiResponse(description="Engagement not found"),
        }
    )
    def put(self, request, candidate_id, engagement_id):
        engagement = self.get_object(
            candidate_id, engagement_id, request.user.tenant_id
        )
        if not engagement:
            return error_response("Engagement not found", status_code=404)
        target_job_id = request.data.get('job', engagement.job_id)
        if target_job_id:
            allowed, message, _ = check_protected_action(
                candidate_id=candidate_id,
                tenant_id=request.user.tenant_id,
                action='workflow_allowed_job',
                job_id=target_job_id,
                actor_user_id=request.user.id,
            )
            if not allowed:
                return error_response(message, status_code=status.HTTP_403_FORBIDDEN)

        effective_mode = _resolve_workflow_mode(
            request.user,
            candidate=engagement.candidate,
            job=engagement.job
        )
        if effective_mode == 'manual' and request.data.get('auto_run') is True:
            return error_response(
                "Manual workflow mode does not allow automated stage actions.",
                status_code=403
            )

        old_stage = engagement.stage
        stage_changed = 'stage' in request.data and request.data['stage'] != old_stage
        stage_note = None
        if stage_changed:
            stage_note, note_error = _require_stage_note(request.data)
            if note_error:
                return note_error
        serializer = CandidateEngagementSerializer(
            engagement, data=request.data, partial=True
        )
        if serializer.is_valid():
            updated = serializer.save(last_activity_at=timezone.now())
            candidate_updates = {'last_activity_at': timezone.now()}
            if updated.job_id is None:
                candidate_updates['engagement_stage'] = updated.stage
                candidate_updates['is_in_active_work'] = updated.is_active
            else:
                from apps.candidates.signals import transition_candidate_to_job_track
                transition_candidate_to_job_track(
                    candidate_id=candidate_id,
                    tenant_id=request.user.tenant_id,
                    job_id=updated.job_id,
                )
                candidate_updates['is_in_active_work'] = False
                candidate_updates['active_job_id'] = updated.job_id
            Candidate.objects.filter(id=candidate_id).update(**candidate_updates)
            # Emit stage change event if stage changed
            if stage_changed:
                CandidateTimelineEvent.objects.create(
                    tenant_id=request.user.tenant_id,
                    candidate_id=candidate_id,
                    engagement=updated,
                    event_type='engagement.stage_changed',
                    actor=request.user,
                    payload={
                        'from_stage': old_stage,
                        'to_stage': updated.stage,
                        'note': stage_note,
                        'changed_by': str(request.user.id),
                        'changed_at': timezone.now().isoformat(),
                    },
                    source='user'
                )
            return success_response({
                'engagement': serializer.data,
                'effective_workflow_mode': effective_mode,
                'workflow_behavior': _workflow_behavior(effective_mode),
            })
        return error_response(serializer.errors)


class CandidateEngagementCloseView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Engagement closed"),
            404: OpenApiResponse(description="Engagement not found"),
        }
    )
    def post(self, request, candidate_id, engagement_id):
        try:
            engagement = CandidateEngagement.objects.get(
                id=engagement_id,
                candidate_id=candidate_id,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except CandidateEngagement.DoesNotExist:
            return error_response("Engagement not found", status_code=404)

        engagement.is_active = False
        engagement.closed_at = timezone.now()
        engagement.closure_reason = request.data.get('closure_reason', '')
        stage_note, note_error = _require_stage_note(request.data)
        if note_error:
            return note_error
        old_stage = engagement.stage
        final_stage = request.data.get('final_stage')
        if not final_stage:
            final_stage = 'nurture' if engagement.job_id is None else 'rejected'
        if engagement.job_id is None and final_stage not in GENERAL_CANDIDATE_STAGES:
            return error_response(
                "General engagement can only close to pre-job stages.",
                {'allowed_stages': list(GENERAL_CANDIDATE_STAGES)}
            )
        if engagement.job_id is not None and final_stage not in JOB_CANDIDATE_STAGES:
            return error_response(
                "Job-specific engagement can only close to post-submission stages.",
                {'allowed_stages': list(JOB_CANDIDATE_STAGES)}
            )
        engagement.stage = final_stage
        engagement.save()
        candidate_updates = {'last_activity_at': timezone.now()}
        if engagement.job_id is None:
            candidate_updates['is_in_active_work'] = False
            candidate_updates['engagement_stage'] = final_stage
            if final_stage in ['nurture', 'dormant']:
                candidate_updates['lifecycle_state'] = final_stage
        Candidate.objects.filter(id=candidate_id).update(**candidate_updates)

        CandidateTimelineEvent.objects.create(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate_id,
            engagement=engagement,
            event_type='engagement.closed',
            actor=request.user,
            payload={
                'closure_reason': engagement.closure_reason,
                'from_stage': old_stage,
                'to_stage': final_stage,
                'note': stage_note,
                'changed_by': str(request.user.id),
                'changed_at': timezone.now().isoformat(),
            },
            source='user'
        )
        return success_response(
            CandidateEngagementSerializer(engagement).data
        )


class CandidateEngagementReviveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Engagement revived"),
            404: OpenApiResponse(description="Engagement not found"),
        }
    )
    def post(self, request, candidate_id, engagement_id):
        try:
            old_engagement = CandidateEngagement.objects.get(
                id=engagement_id,
                candidate_id=candidate_id,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except CandidateEngagement.DoesNotExist:
            return error_response("Engagement not found", status_code=404)

        # Enforce: one active general presence maximum per candidate.
        existing_general = CandidateEngagement.objects.filter(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate_id,
            job__isnull=True,
            is_active=True,
            is_deleted=False,
        ).order_by('-started_at').first()
        if existing_general:
            return success_response(
                CandidateEngagementSerializer(existing_general).data,
                message="Candidate already has an active general presence."
            )

        # Create new active engagement linked to old one
        new_engagement = CandidateEngagement.objects.create(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate_id,
            engagement_type='revival',
            stage='new_lead',
            priority=request.data.get('priority', 'warm'),
            is_active=True,
            owner_user=request.user,
            resurrected_from=old_engagement,
            created_by=request.user,
            last_activity_at=timezone.now()
        )
        candidate = Candidate.objects.filter(id=candidate_id).first()
        revive_updates = {
            'is_in_active_work': True,
            'engagement_stage': 'new_lead',
            'lifecycle_state': 'active',
            'last_activity_at': timezone.now(),
            'candidate_pool': 'GENERAL',
            'candidate_state': 'REVIVED' if (candidate and candidate.is_general_pool_used) else 'NEW_LEAD',
        }
        Candidate.objects.filter(id=candidate_id).update(**revive_updates)

        CandidateTimelineEvent.objects.create(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate_id,
            engagement=new_engagement,
            event_type='engagement.revived',
            actor=request.user,
            payload={
                'revived_from_engagement': str(old_engagement.id),
                'original_stage': old_engagement.stage
            },
            source='user'
        )
        return success_response(
            CandidateEngagementSerializer(new_engagement).data,
            status_code=201
        )


class ActiveCandidatesView(APIView):
    """Recruiter-first Active Work surface: board + focus + follow-up queue."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mode = request.query_params.get('mode', 'focus')
        priority = request.query_params.get('priority')
        stage = request.query_params.get('stage')
        follow_up_overdue = request.query_params.get('follow_up_overdue')
        owner = request.query_params.get('owner')

        qs = CandidateEngagement.objects.filter(
            tenant_id=request.user.tenant_id,
            is_active=True,
            is_deleted=False,
        ).filter(
            Q(job__isnull=True, candidate__candidate_pool='GENERAL') |
            Q(job__isnull=False)
        ).select_related('candidate', 'owner_user', 'job')

        if priority:
            qs = qs.filter(priority=priority)
        if stage:
            qs = qs.filter(stage=stage)
        if follow_up_overdue == 'true':
            qs = qs.filter(follow_up_at__lt=timezone.now())
        if owner == 'me':
            qs = qs.filter(owner_user=request.user)
        elif owner and owner != 'me':
            try:
                qs = qs.filter(owner_user_id=uuid.UUID(owner))
            except (ValueError, AttributeError):
                pass

        qs = qs.order_by('-last_activity_at')
        serializer = CandidateEngagementSerializer(qs, many=True).data

        if mode == 'board':
            board = {s: [] for s in ACTIVE_WORK_STAGES}
            for item in serializer:
                stage_key = item.get('stage') or 'new_lead'
                if stage_key not in board:
                    board[stage_key] = []
                board[stage_key].append(item)
            return success_response({
                'mode': 'board',
                'stages': ACTIVE_WORK_STAGES,
                'board': board,
                'count': qs.count(),
            })

        if mode == 'follow_up_queue':
            queue_qs = qs.filter(follow_up_at__isnull=False).order_by('follow_up_at')
            queue = CandidateEngagementSerializer(queue_qs, many=True).data
            return success_response({
                'mode': 'follow_up_queue',
                'queue': queue,
                'count': queue_qs.count(),
            })

        # Default: Focus Mode buckets
        now = timezone.now()
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        stale_days = 21
        tenant_policy = CandidateWorkflowPolicy.objects.filter(
            tenant_id=request.user.tenant_id,
            team_id__isnull=True,
            recruiter_user_id__isnull=True,
            is_active=True
        ).first()
        if tenant_policy:
            stale_days = tenant_policy.candidate_stale_days

        focus = {
            'follow_up_due_today': [],
            'hot_candidates': [],
            'newly_sourced': [],
            'ready_for_submission': [],
            'needs_review': [],
            'stuck_candidates': [],
            'missing_information': [],
        }

        for e in qs:
            row = CandidateEngagementSerializer(e).data
            c = e.candidate

            if e.follow_up_at and e.follow_up_at <= today_end:
                focus['follow_up_due_today'].append(row)
            if e.priority == 'hot' or (c.readiness_score or 0) >= 80 or (c.fit_score or 0) >= 80:
                focus['hot_candidates'].append(row)
            if e.started_at >= (now - timedelta(days=3)):
                focus['newly_sourced'].append(row)
            if e.stage in ['qualified'] and (c.readiness_score or 0) >= 60:
                focus['ready_for_submission'].append(row)
            if c.duplicate_review_status in ['pending_review', 'confirmed_duplicate'] or c.profile_completeness < 60:
                focus['needs_review'].append(row)
            if (e.last_activity_at and e.last_activity_at <= (now - timedelta(days=stale_days))):
                focus['stuck_candidates'].append(row)
            if not c.email and not c.phone and not c.phone_number:
                focus['missing_information'].append(row)

        return success_response({
            'mode': 'focus',
            'focus': focus,
            'count': qs.count(),
        })


class CandidateEngagementTimelineView(APIView):
    """Full immutable timeline for a candidate"""
    permission_classes = [IsAuthenticated]

    def get(self, request, candidate_id):
        engagement_id = request.query_params.get('engagement_id')

        qs = CandidateTimelineEvent.objects.filter(
            candidate_id=candidate_id,
            tenant_id=request.user.tenant_id
        ).select_related('actor', 'engagement')

        if engagement_id:
            qs = qs.filter(engagement_id=engagement_id)

        qs = qs.order_by('-created_at')

        serializer = CandidateTimelineEventSerializer(qs, many=True)
        return success_response(serializer.data)


class CandidateDatabaseView(APIView):
    """System-of-record layer with smart rows and enterprise saved views."""
    permission_classes = [IsAuthenticated, require_permission('candidates.candidate.view')]

    def get(self, request):
        visible_candidate_ids_from_apps = Application.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).values_list('candidate_id', flat=True)

        visible_candidate_ids_from_engagements = CandidateEngagement.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).values_list('candidate_id', flat=True)

        qs = Candidate.objects.filter(
            is_deleted=False
        ).filter(
            Q(tenant_id=request.user.tenant_id) |
            Q(id__in=visible_candidate_ids_from_apps) |
            Q(id__in=visible_candidate_ids_from_engagements)
        )

        view_name = request.query_params.get('view', 'all_candidates')
        stale_days = 21
        tenant_policy = CandidateWorkflowPolicy.objects.filter(
            tenant_id=request.user.tenant_id,
            team_id__isnull=True,
            recruiter_user_id__isnull=True,
            is_active=True
        ).first()
        if tenant_policy:
            stale_days = tenant_policy.candidate_stale_days

        if view_name and view_name != 'all_candidates':
            qs = _apply_saved_view(qs, view_name, stale_days=stale_days)

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(current_title__icontains=search) |
                Q(current_company__icontains=search) |
                Q(source_subtype__icontains=search)
            )

        source_type = request.query_params.get('source_type')
        if source_type:
            qs = qs.filter(source_type=source_type)
        source_subtype = request.query_params.get('source_subtype')
        if source_subtype:
            qs = qs.filter(source_subtype=source_subtype)
        stage = request.query_params.get('engagement_stage')
        if stage:
            qs = qs.filter(engagement_stage=stage)
        owner = request.query_params.get('owner')
        if owner == 'me':
            qs = qs.filter(owner_user_id=request.user.id)
        elif owner:
            try:
                qs = qs.filter(owner_user_id=uuid.UUID(owner))
            except ValueError:
                pass
        passport_linked = request.query_params.get('passport_linked')
        if passport_linked == 'true':
            qs = qs.filter(Q(passport_linked=True) | Q(passport_id__isnull=False))
        duplicates = request.query_params.get('duplicates')
        if duplicates == 'true':
            qs = qs.filter(Q(is_duplicate=True) | Q(duplicate_of__isnull=False))
        if request.query_params.get('active_work') == 'true':
            qs = qs.filter(is_in_active_work=True)
        protection_status = request.query_params.get('protection_status')
        if protection_status in ['protected', 'not_protected']:
            active_protected_candidate_ids = CandidateTenantRight.objects.filter(
                target_tenant_id=request.user.tenant_id,
                relationship_type='protected',
                status='active',
                is_deleted=False,
            ).filter(
                Q(protected_until__isnull=True) | Q(protected_until__gt=timezone.now())
            ).values_list('candidate_id', flat=True)
            if protection_status == 'protected':
                qs = qs.filter(id__in=active_protected_candidate_ids)
            else:
                qs = qs.exclude(id__in=active_protected_candidate_ids)

        total = qs.count()
        limit = min(int(request.query_params.get('limit', 50)), 200)
        offset = max(int(request.query_params.get('offset', 0)), 0)
        qs = list(qs.order_by('-last_activity_at', '-updated_at')[offset:offset + limit])

        candidate_ids = [c.id for c in qs]
        summary_map = {}
        owner_name_map = {}
        if candidate_ids:
            summary_rows = CandidateEngagement.objects.filter(
                tenant_id=request.user.tenant_id,
                candidate_id__in=candidate_ids,
                job__isnull=False,
                is_active=True,
                is_deleted=False,
            ).values('candidate_id', 'stage').annotate(count=Count('id'))

            for row in summary_rows:
                cid = str(row['candidate_id'])
                stage = row['stage']
                summary_map.setdefault(cid, {})
                summary_map[cid][stage] = row['count']

            owner_ids = {c.owner_user_id for c in qs if c.owner_user_id}
            if owner_ids:
                owners = CustomUser.objects.filter(id__in=owner_ids).values('id', 'first_name', 'last_name', 'email')
                for owner in owners:
                    full_name = f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip()
                    owner_name_map[str(owner['id'])] = full_name or owner.get('email')

        return success_response(
            data={
                'items': [
                    _candidate_smart_row(
                        c,
                        summary_map.get(str(c.id), {}),
                        owner_name_map,
                        request.user.tenant_id,
                    ) for c in qs
                ],
                'view': view_name,
                'available_views': [
                    'all_candidates', 'active_work', 'recently_added', 'passport_linked',
                    'agency_submitted', 'duplicates', 'dormant', 'follow_up_due',
                    'ready_to_submit', 'missing_contact_info', 'general_pool'
                ]
            },
            meta={'total': total, 'limit': limit, 'offset': offset},
            message="Candidate database retrieved."
        )


class CandidateSavedViewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        base_qs = Candidate.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )
        stale_days = 21
        tenant_policy = CandidateWorkflowPolicy.objects.filter(
            tenant_id=request.user.tenant_id,
            team_id__isnull=True,
            recruiter_user_id__isnull=True,
            is_active=True
        ).first()
        if tenant_policy:
            stale_days = tenant_policy.candidate_stale_days

        views = [
            ('all_candidates', 'All Candidates'),
            ('active_work', 'Active Work'),
            ('recently_added', 'Recently Added'),
            ('passport_linked', 'Passport Linked'),
            ('agency_submitted', 'Agency Submitted'),
            ('duplicates', 'Duplicates'),
            ('dormant', 'Dormant'),
            ('follow_up_due', 'Follow-up Due'),
            ('ready_to_submit', 'Ready to Submit'),
            ('missing_contact_info', 'Missing Contact Info'),
        ]
        data = []
        for key, label in views:
            if key == 'all_candidates':
                count = base_qs.count()
            else:
                count = _apply_saved_view(base_qs, key, stale_days=stale_days).count()
            data.append({'key': key, 'label': label, 'count': count})

        return success_response(
            data={'views': data},
            message="Saved views retrieved."
        )


class CandidateWorkflowPolicyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scope = request.query_params.get('scope', 'tenant')
        team_id = request.query_params.get('team_id')
        recruiter_user_id = request.query_params.get('recruiter_user_id')

        filters = {'tenant_id': request.user.tenant_id, 'is_active': True}
        if scope == 'tenant':
            filters.update({'team_id__isnull': True, 'recruiter_user_id__isnull': True})
        elif scope == 'team':
            filters.update({'team_id': team_id, 'recruiter_user_id__isnull': True})
        elif scope == 'recruiter':
            filters.update({'team_id__isnull': True, 'recruiter_user_id': recruiter_user_id})

        policy = CandidateWorkflowPolicy.objects.filter(**filters).first()
        if not policy:
            return success_response(
                data={
                    'policy': None,
                    'effective_workflow_mode': _resolve_workflow_mode(request.user),
                    'workflow_behavior': _workflow_behavior(_resolve_workflow_mode(request.user)),
                },
                message="No workflow policy configured for scope."
            )

        return success_response(
            data={
                'policy': CandidateWorkflowPolicySerializer(policy).data,
                'effective_workflow_mode': _resolve_workflow_mode(request.user),
                'workflow_behavior': _workflow_behavior(_resolve_workflow_mode(request.user)),
            },
            message="Workflow policy retrieved."
        )

    def put(self, request):
        scope = request.data.get('scope', 'tenant')
        team_id = request.data.get('team_id')
        recruiter_user_id = request.data.get('recruiter_user_id')

        policy, _ = CandidateWorkflowPolicy.objects.get_or_create(
            tenant_id=request.user.tenant_id,
            team_id=team_id if scope == 'team' else None,
            recruiter_user_id=recruiter_user_id if scope == 'recruiter' else None,
            defaults={'created_by': request.user.id}
        )
        payload = request.data.copy()
        payload.pop('scope', None)
        serializer = CandidateWorkflowPolicySerializer(
            policy, data=payload, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return success_response(
                data={'policy': serializer.data},
                message="Workflow policy updated."
            )
        return error_response("Validation failed.", serializer.errors)


class CandidateCommandCenterView(APIView):
    """Candidate command center payload for tabs + sticky actions."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            candidate = Candidate.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Candidate.DoesNotExist:
            return error_response("Candidate not found.", status_code=404)

        engagements = CandidateEngagement.objects.filter(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate.id,
            is_deleted=False
        ).order_by('-updated_at')
        notes = CandidateNote.objects.filter(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate.id,
            is_deleted=False
        ).select_related('engagement').order_by('-created_at')
        timeline = CandidateTimelineEvent.objects.filter(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate.id
        ).select_related('engagement', 'actor').order_by('-created_at')
        profile = CandidateProfile.objects.filter(candidate_id=candidate.id).first()
        engagements_list = list(engagements[:50])
        timeline_list = list(timeline[:100])
        notes_list = list(notes[:100])

        structured_activity = [_structured_activity_item(e) for e in timeline_list]
        structured_notes = [_structured_note_item(n) for n in notes_list]

        return success_response(
            data={
                'candidate': {
                    **CandidateDetailSerializer(candidate).data,
                    **protection_badge_payload(
                        candidate_id=candidate.id,
                        target_tenant_id=request.user.tenant_id,
                    ),
                },
                'tabs': {
                    'overview': CandidateSerializer(candidate).data,
                    'activity_timeline': CandidateTimelineEventSerializer(timeline_list[:50], many=True).data,
                    'structured_activity': structured_activity,
                    'notes': CandidateNoteSerializer(notes_list[:50], many=True).data,
                    'structured_notes': structured_notes,
                    'jobs_matches': [{'job_id': str(e.job_id), 'stage': e.stage} for e in engagements_list if e.job_id],
                    'engagement': CandidateEngagementSerializer(engagements_list, many=True).data,
                    'documents': {
                        'resume_url': candidate.resume_url,
                        'profile_cv_url': profile.cv_url if profile else ''
                    },
                    'communication': {
                        'last_contact_at': candidate.last_contact_at,
                        'next_follow_up_at': candidate.next_follow_up_at,
                    },
                    'history': CandidateTimelineEventSerializer(timeline_list[:50], many=True).data,
                    'automations': {
                        'workflow_mode': candidate.workflow_mode,
                        'automation_enabled': candidate.automation_enabled,
                        'auto_nurture_enabled': candidate.auto_nurture_enabled,
                        'auto_followup_enabled': candidate.auto_followup_enabled,
                        'auto_stage_suggestions_enabled': candidate.auto_stage_suggestions_enabled,
                        'behavior': _workflow_behavior(candidate.workflow_mode),
                    }
                },
                'sticky_actions': [
                    'add_to_active_work',
                    'call',
                    'email',
                    'schedule',
                    'submit_to_job',
                    'add_note',
                    'change_stage',
                ]
            },
            message="Candidate command center retrieved."
        )
