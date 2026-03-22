from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from apps.candidates.models import Candidate, CandidateProfile, CandidateNote
from apps.candidates.serializers import (
    CandidateSerializer, CandidateDetailSerializer,
    CandidateProfileSerializer, CandidateNoteSerializer,
)
from apps.core.responses import success_response, error_response


class CandidateListView(APIView):
    permission_classes = [IsAuthenticated]

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
        # Deduplication check
        email = request.data.get('email', '').strip().lower()
        phone = request.data.get('phone', '').strip()

        existing = None
        if email:
            existing = Candidate.objects.filter(
                email__iexact=email, is_deleted=False
            ).first()
        if not existing and phone:
            existing = Candidate.objects.filter(
                phone=phone, is_deleted=False
            ).first()

        if existing:
            return error_response(
                f"Candidate already exists with this "
                f"{'email' if email else 'phone'}.",
                status_code=status.HTTP_409_CONFLICT,
                data={'candidate_id': str(existing.id)}
            )

        payload = request.data.copy()
        entry_type = payload.pop('entry_type', 'manual')
        send_invite = payload.pop('send_invite', False)

        serializer = CandidateSerializer(data=payload)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        candidate = serializer.save(
            tenant_id=request.user.tenant_id,
            owner_user_id=request.user.id,
            owner_tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )

        # Auto-create empty profile
        CandidateProfile.objects.create(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate.id,
            created_by=request.user.id,
        )

        if entry_type in ['invite', 'quick_add']:
            import secrets
            from datetime import timedelta
            from django.utils import timezone
            candidate.profile_status = 'draft'
            candidate.initial_entry_type = 'invite'
            candidate.claim_token = secrets.token_urlsafe(32)
            candidate.claim_token_expires_at = (
                timezone.now() + timedelta(days=30)
            )
        else:
            candidate.profile_status = 'partial'
            candidate.initial_entry_type = 'manual'

        send_invite_bool = send_invite
        if isinstance(send_invite, str):
            send_invite_bool = send_invite.lower() in ['1', 'true', 'yes', 'on']

        if send_invite_bool and candidate.claim_token:
            from django.utils import timezone
            candidate.account_status = 'invited'
            candidate.invite_sent_at = timezone.now()
            print(
                f"[STUB] Invite: "
                f"/candidate/complete/{candidate.claim_token}"
            )

        candidate.save()

        response_data = {
            'candidate': CandidateSerializer(candidate).data
        }
        if candidate.claim_token:
            response_data['claim_token'] = candidate.claim_token
            response_data['claim_link'] = (
                f"/candidate/complete/{candidate.claim_token}"
            )

        return success_response(
            data=response_data,
            message="Candidate created.",
            status_code=status.HTTP_201_CREATED
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

        return success_response(
            data={'candidate': CandidateDetailSerializer(candidate).data},
            message="Candidate retrieved."
        )

    def put(self, request, pk):
        candidate = self.get_object(request, pk)
        if not candidate:
            return error_response("Candidate not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = CandidateSerializer(candidate, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
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
