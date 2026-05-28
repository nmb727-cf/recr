import secrets
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.passport.models import TalentPassport, PassportAccessLog, PassportRevocation
from apps.passport.serializers import (
    TalentPassportSerializer, TalentPassportPublicSerializer,
    PassportAccessLogSerializer,
)
from apps.core.responses import success_response, error_response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.candidates.identity_service import resolve_candidate_identity, merge_candidate_payload


class MyPassportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            passport = TalentPassport.objects.get(
                user_id=request.user.id,
                is_deleted=False
            )
            return success_response(
                data={'passport': TalentPassportSerializer(passport).data},
                message="Passport retrieved."
            )
        except TalentPassport.DoesNotExist:
            return error_response(
                "Passport not found. Please create your passport.",
                status_code=status.HTTP_404_NOT_FOUND
            )

    def put(self, request):
        try:
            passport = TalentPassport.objects.get(
                user_id=request.user.id,
                is_deleted=False
            )
        except TalentPassport.DoesNotExist:
            # Auto-create passport on first onboarding save
            passport = TalentPassport(user_id=request.user.id)

        # ── Append-safe merge ─────────────────────────────────────────────────
        # Build a request-data dict that:
        #   1. Skips empty strings for text fields — never erase existing data
        #   2. Unions list fields (skills, languages, etc.) instead of replacing
        # This makes the PUT idempotent for blank/partial submissions and safe
        # for multi-step onboarding where each step only sends its own fields.
        merged = _merge_passport_data(passport, request.data)

        serializer = TalentPassportSerializer(passport, data=merged, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        passport = serializer.save(user_id=request.user.id)

        # Calculate completeness score
        passport.completeness_score = _calculate_completeness(passport)

        # Link passport ↔ Candidate if not already linked.
        # A Candidate record may exist (pre-added by recruiter) or may be created
        # lazily here for direct-signup candidates who have never been in the pipeline.
        _link_passport_to_candidate(passport, request.user)

        passport.save(update_fields=['completeness_score', 'candidate_id'])

        return success_response(
            data={'passport': TalentPassportSerializer(passport).data},
            message="Passport updated."
        )


# Simple string arrays — use union-merge (new items appended, no duplicates)
_UNION_LIST_FIELDS = frozenset([
    'skills', 'languages', 'preferred_locations', 'preferred_job_types',
    'preferred_industries',
])

# Complex object arrays (items have IDs) — always replace wholesale so edit/delete work
_REPLACE_LIST_FIELDS = frozenset([
    'work_history', 'education', 'certifications', 'projects',
    'publications', 'awards', 'volunteer_work', 'test_scores',
    'references', 'featured_media',
])

# Text fields where an empty string means "not provided" — never overwrite with blank
_TEXT_FIELDS = frozenset([
    'headline', 'summary', 'profile_photo_url', 'cover_image_url',
    'video_intro_url', 'current_title', 'current_company',
    'current_location_city', 'current_location_country',
    'current_cv_url', 'current_cv_filename',
    'linkedin_url', 'github_url', 'portfolio_url',
    'twitter_url', 'behance_url', 'dribbble_url',
])


def _merge_passport_data(passport, incoming: dict) -> dict:
    """
    Produce a merged data dict to pass to the serializer.

    Rules:
      • Text fields: skip if incoming is an empty string and field already has a value.
      • List fields: union of existing + incoming (deduplicated, order preserved).
      • All other fields (numbers, booleans, dates): pass through as-is.

    This ensures a partial submission (e.g. only step 1 fields) never erases
    data saved by a previous step or by a recruiter's quick-add form.
    """
    result = dict(incoming)

    for field in _TEXT_FIELDS:
        if field not in incoming:
            continue
        incoming_val = incoming[field]
        existing_val = getattr(passport, field, None)
        # Skip empty string if field already has a non-empty value
        if (incoming_val == '' or incoming_val is None) and existing_val:
            del result[field]

    # Union-merge: simple string arrays — append new items, keep existing order
    for field in _UNION_LIST_FIELDS:
        if field not in incoming:
            continue
        incoming_list = incoming[field] if isinstance(incoming[field], list) else []
        existing_list = getattr(passport, field, None) or []
        merged_list = list(existing_list)
        seen = set(str(x).lower() for x in existing_list)
        for item in incoming_list:
            key = str(item).lower()
            if key and key not in seen:
                merged_list.append(item)
                seen.add(key)
        result[field] = merged_list

    # Replace: complex object arrays — pass through as-is (edit/delete must work)
    for field in _REPLACE_LIST_FIELDS:
        if field not in incoming:
            continue
        result[field] = incoming[field] if isinstance(incoming[field], list) else []

    return result


def _calculate_completeness(passport):
    score = 0
    if passport.headline: score += 10
    if passport.summary: score += 10
    if passport.profile_photo_url: score += 5
    if passport.current_title: score += 10
    if passport.skills: score += 15
    if passport.work_history: score += 20
    if passport.education: score += 10
    if passport.current_cv_url: score += 10
    if passport.linkedin_url: score += 5
    if passport.certifications: score += 5
    return min(score, 100)


def _link_passport_to_candidate(passport, user):
    """
    Ensure TalentPassport.candidate_id is set and the matching Candidate record
    has passport_id + passport_linked set back.

    Lookup order:
      1. Candidate.user_id == user.id  (fast path)
      2. Email match (recruiter pre-added)

    If no Candidate record exists at all (fresh direct-signup), create a minimal
    one so the passport has something to link to.
    """
    resolution = resolve_candidate_identity(
        email=user.email,
        phone=getattr(user, 'phone', '') or '',
        user=user,
        passport_id=passport.id,
        tenant_id=getattr(user, 'tenant_id', None),
        create_if_missing=True,
        allow_cross_tenant=True,
        actor_user_id=user.id,
        ensure_tenant_association_flag=bool(getattr(user, 'tenant_id', None)),
        ensure_visibility=False,
        source='passport_self_link',
        candidate_defaults={
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'email': user.email,
            'phone': getattr(user, 'phone', '') or '',
            'source': 'self',
            'source_type': 'direct',
            'account_status': 'active',
            'profile_status': 'partial',
            'initial_entry_type': 'self',
            'owner_tenant_id': getattr(user, 'tenant_id', None),
            'owner_user_id': user.id,
            'passport_id': passport.id,
            'passport_linked': True,
        },
    )
    candidate = resolution.candidate

    # Sync passport → candidate
    if not passport.candidate_id:
        passport.candidate_id = candidate.id

    # Sync candidate → passport
    update_fields = []
    if not candidate.passport_id or str(candidate.passport_id) != str(passport.id):
        candidate.passport_id = passport.id
        update_fields.append('passport_id')
    if not candidate.passport_linked:
        candidate.passport_linked = True
        update_fields.append('passport_linked')
    if update_fields:
        update_fields.append('updated_at')
        candidate.save(update_fields=update_fields)


class MyPassportAccessLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            passport = TalentPassport.objects.get(
                user_id=request.user.id,
                is_deleted=False
            )
        except TalentPassport.DoesNotExist:
            return error_response("Passport not found.", status_code=status.HTTP_404_NOT_FOUND)

        logs = PassportAccessLog.objects.filter(
            passport_id=passport.id
        ).order_by('-accessed_at')[:50]

        return success_response(
            data={'access_logs': PassportAccessLogSerializer(logs, many=True).data},
            message="Access log retrieved."
        )


class MyPassportRevokeAccessView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            passport = TalentPassport.objects.get(
                user_id=request.user.id,
                is_deleted=False
            )
        except TalentPassport.DoesNotExist:
            return error_response("Passport not found.", status_code=status.HTTP_404_NOT_FOUND)

        tenant_id = request.data.get('tenant_id')
        reason = request.data.get('reason', '')

        if not tenant_id:
            return error_response("tenant_id is required.")

        PassportRevocation.objects.create(
            passport_id=passport.id,
            revoked_from_tenant_id=tenant_id,
            reason=reason,
            revoked_by=request.user.id,
        )

        # Mark access logs as revoked
        PassportAccessLog.objects.filter(
            passport_id=passport.id,
            accessed_by_tenant_id=tenant_id,
            revoked_at__isnull=True
        ).update(revoked_at=timezone.now(), revoked_by=request.user.id)

        return success_response(message="Access revoked successfully.")


class MyPassportRevokeAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            passport = TalentPassport.objects.get(
                user_id=request.user.id,
                is_deleted=False
            )
        except TalentPassport.DoesNotExist:
            return error_response("Passport not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Revoke all access
        PassportAccessLog.objects.filter(
            passport_id=passport.id,
            revoked_at__isnull=True
        ).update(revoked_at=timezone.now(), revoked_by=request.user.id)

        # Regenerate share link token
        passport.share_link_token = secrets.token_urlsafe(32)
        passport.save(update_fields=['share_link_token'])

        return success_response(message="All access revoked and share link regenerated.")


class MyPassportShareLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            passport = TalentPassport.objects.get(
                user_id=request.user.id,
                is_deleted=False
            )
        except TalentPassport.DoesNotExist:
            return error_response("Passport not found.", status_code=status.HTTP_404_NOT_FOUND)

        share_url = f"/passport/public/{passport.share_link_token}"
        return success_response(
            data={
                'share_url': share_url,
                'token': passport.share_link_token,
            },
            message="Share link retrieved."
        )


class MyPassportRegenerateLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            passport = TalentPassport.objects.get(
                user_id=request.user.id,
                is_deleted=False
            )
        except TalentPassport.DoesNotExist:
            return error_response("Passport not found.", status_code=status.HTTP_404_NOT_FOUND)

        passport.share_link_token = secrets.token_urlsafe(32)
        passport.save(update_fields=['share_link_token'])

        share_url = f"/passport/public/{passport.share_link_token}"
        return success_response(
            data={
                'share_url': share_url,
                'token': passport.share_link_token,
            },
            message="Share link regenerated."
        )

# Maps each visibility_settings key → public serializer fields to strip when False.
# Defaults (when key absent) are all True (show everything).
_VISIBILITY_FIELD_MAP = {
    'show_availability':    ['is_actively_looking', 'open_to_work'],
    'show_notice_period':   ['notice_period_days'],
    'show_work_mode':       ['preferred_work_mode'],
    'show_certifications':  ['certifications'],
    'show_projects':        ['projects'],
    'show_publications':    ['publications'],
    'show_awards':          ['awards'],
    'show_volunteer':       ['volunteer_work'],
    # show_salary / show_contact: those fields are not in the public serializer,
    # kept here as no-ops for forward compatibility.
}


def _apply_visibility(data: dict, visibility: dict) -> dict:
    """
    Strip fields from serialized public passport data based on the candidate's
    visibility_settings. Unknown keys default to visible (True).
    """
    result = dict(data)
    for setting_key, fields in _VISIBILITY_FIELD_MAP.items():
        if not visibility.get(setting_key, True):
            for field in fields:
                result.pop(field, None)
    return result


@extend_schema(
    responses={
        200: OpenApiResponse(description="Success"),
        404: OpenApiResponse(description="Passport not found or link has expired."),
    }
)

class PublicPassportView(APIView):
    permission_classes = [AllowAny]

    def _rate_limit_exceeded(self, request, token):
        ip_addr = request.META.get('REMOTE_ADDR', '') or 'unknown'
        key = f'public_passport:{token}:{ip_addr}'
        ttl_seconds = int(getattr(settings, 'PUBLIC_PASSPORT_RATE_WINDOW_SECONDS', 60))
        limit = int(getattr(settings, 'PUBLIC_PASSPORT_RATE_LIMIT', 30))
        current = cache.get(key)
        if current is None:
            cache.set(key, 1, timeout=ttl_seconds)
            return False
        if int(current) >= limit:
            return True
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, int(current) + 1, timeout=ttl_seconds)
        return False

    def get(self, request, token):
        if self._rate_limit_exceeded(request, token):
            return error_response("Too many requests. Please retry shortly.", status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        try:
            passport = TalentPassport.objects.get(
                share_link_token=token,
                is_active=True,
                is_deleted=False
            )
        except TalentPassport.DoesNotExist:
            return error_response(
                "Passport not found or link has expired.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Log access
        PassportAccessLog.objects.create(
            passport_id=passport.id,
            accessed_by_user_id=request.user.id if request.user.is_authenticated else None,
            accessed_by_tenant_id=request.user.tenant_id if request.user.is_authenticated else None,
            access_type='view',
            ip_address=request.META.get('REMOTE_ADDR', ''),
        )

        # Increment view count
        passport.view_count += 1
        passport.last_viewed_at = timezone.now()
        passport.save(update_fields=['view_count', 'last_viewed_at'])

        # Apply candidate's visibility preferences before returning
        serialized = dict(TalentPassportPublicSerializer(passport).data)
        serialized = _apply_visibility(serialized, passport.visibility_settings or {})

        return success_response(
            data={'passport': serialized},
            message="Passport retrieved."
        )


class PassportImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        passport_token = request.data.get('passport_token')
        if not passport_token:
            return error_response("passport_token is required.")

        try:
            passport = TalentPassport.objects.get(
                share_link_token=passport_token,
                is_active=True,
                is_deleted=False
            )
        except TalentPassport.DoesNotExist:
            return error_response(
                "Invalid passport token.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if PassportRevocation.objects.filter(
            passport_id=passport.id,
            revoked_from_tenant_id=request.user.tenant_id,
        ).exists():
            return error_response(
                "This passport has been revoked for your tenant.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Log import access
        PassportAccessLog.objects.create(
            passport_id=passport.id,
            accessed_by_user_id=request.user.id,
            accessed_by_tenant_id=request.user.tenant_id,
            access_type='import',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            imported_to_system=True,
        )

        # Resolve passport owner details (name, email) from their user account
        from apps.accounts.models import CustomUser
        from apps.candidates.models import CandidateProfile

        passport_owner = None
        owner_first_name = ''
        owner_last_name = ''
        owner_email = ''
        if passport.user_id:
            passport_owner = CustomUser.objects.filter(id=passport.user_id).first()
            if passport_owner:
                owner_first_name = passport_owner.first_name or ''
                owner_last_name = passport_owner.last_name or ''
                owner_email = passport_owner.email or ''

        resolution = resolve_candidate_identity(
            email=owner_email,
            passport_id=passport.id,
            tenant_id=request.user.tenant_id,
            create_if_missing=True,
            allow_cross_tenant=True,
            actor_user_id=request.user.id,
            ensure_tenant_association_flag=True,
            ensure_visibility=True,
            source='passport_import',
            candidate_defaults={
                'tenant_id': request.user.tenant_id,
                'first_name': owner_first_name,
                'last_name': owner_last_name,
                'email': owner_email,
                'current_title': passport.current_title,
                'current_company': passport.current_company,
                'current_location_city': passport.current_location_city,
                'experience_years': passport.experience_years,
                'skills': passport.skills,
                'languages': passport.languages,
                'source': 'passport',
                'source_type': 'passport',
                'initial_entry_type': 'import_passport',
                'passport_id': passport.id,
                'passport_linked': True,
                'owner_user_id': request.user.id,
                'owner_tenant_id': request.user.tenant_id,
                'created_by': request.user.id,
                'candidate_state': 'NEW_LEAD',
                'candidate_pool': 'GENERAL',
                'is_general_pool_used': False,
            },
        )
        candidate = resolution.candidate
        created = resolution.created

        merge_candidate_payload(
            candidate,
            {
                'first_name': owner_first_name,
                'last_name': owner_last_name,
                'email': owner_email,
                'current_title': passport.current_title,
                'current_company': passport.current_company,
                'current_location_city': passport.current_location_city,
                'experience_years': passport.experience_years,
                'skills': passport.skills,
                'languages': passport.languages,
                'passport_id': passport.id,
                'passport_linked': True,
            },
            overwrite=False,
        )
        profile, profile_created = CandidateProfile.objects.get_or_create(
            candidate_id=candidate.id,
            defaults={
                'tenant_id': request.user.tenant_id,
                'created_by': request.user.id,
                'summary': passport.summary,
                'work_experience': passport.work_history,
                'education': passport.education,
                'certifications': passport.certifications,
            },
        )
        if not profile_created:
            changed = False
            if passport.summary and not profile.summary:
                profile.summary = passport.summary
                changed = True
            if passport.work_history and not profile.work_experience:
                profile.work_experience = passport.work_history
                changed = True
            if passport.education and not profile.education:
                profile.education = passport.education
                changed = True
            if passport.certifications and not profile.certifications:
                profile.certifications = passport.certifications
                changed = True
            if changed:
                profile.save(update_fields=['summary', 'work_experience', 'education', 'certifications', 'updated_at'])

        return success_response(
            data={
                'candidate_id': str(candidate.id),
                'import_status': 'created' if created else 'already_exists',
            },
            message="Passport imported successfully."
        )
