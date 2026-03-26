import secrets
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.passport.models import TalentPassport, PassportAccessLog, PassportRevocation
from apps.passport.serializers import (
    TalentPassportSerializer, TalentPassportPublicSerializer,
    PassportAccessLogSerializer,
)
from apps.core.responses import success_response, error_response


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
        passport.save(update_fields=['completeness_score'])

        return success_response(
            data={'passport': TalentPassportSerializer(passport).data},
            message="Passport updated."
        )


# List fields that use union-merge semantics (new items are appended, not replaced)
_LIST_FIELDS = frozenset([
    'skills', 'languages', 'certifications', 'projects', 'publications',
    'awards', 'volunteer_work', 'preferred_locations', 'preferred_job_types',
    'preferred_industries', 'test_scores', 'references', 'work_history',
    'education',
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

    for field in _LIST_FIELDS:
        if field not in incoming:
            continue
        incoming_list = incoming[field] if isinstance(incoming[field], list) else []
        existing_list = getattr(passport, field, None) or []
        # Union: existing first to preserve order, then any new items appended
        merged_list = list(existing_list)
        seen = set(str(x).lower() for x in existing_list)
        for item in incoming_list:
            key = str(item).lower()
            if key and key not in seen:
                merged_list.append(item)
                seen.add(key)
        result[field] = merged_list

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

        share_url = f"/api/v1/passport/public/{passport.share_link_token}/"
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

        share_url = f"/api/v1/passport/public/{passport.share_link_token}/"
        return success_response(
            data={
                'share_url': share_url,
                'token': passport.share_link_token,
            },
            message="Share link regenerated."
        )


class PublicPassportView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
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

        return success_response(
            data={'passport': TalentPassportPublicSerializer(passport).data},
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

        # Log import access
        PassportAccessLog.objects.create(
            passport_id=passport.id,
            accessed_by_user_id=request.user.id,
            accessed_by_tenant_id=request.user.tenant_id,
            access_type='import',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            imported_to_system=True,
        )

        # Create candidate record from passport
        from apps.candidates.models import Candidate, CandidateProfile
        candidate, created = Candidate.objects.get_or_create(
            tenant_id=request.user.tenant_id,
            passport_id=passport.id,
            defaults={
                'first_name': '',
                'last_name': '',
                'email': '',
                'current_title': passport.current_title,
                'current_company': passport.current_company,
                'current_location_city': passport.current_location_city,
                'experience_years': passport.experience_years,
                'skills': passport.skills,
                'source': 'passport',
                'owner_user_id': request.user.id,
                'owner_tenant_id': request.user.tenant_id,
                'created_by': request.user.id,
                'candidate_state': 'NEW_LEAD',
                'candidate_pool': 'GENERAL',
                'is_general_pool_used': False,
            }
        )

        if created:
            CandidateProfile.objects.create(
                tenant_id=request.user.tenant_id,
                candidate_id=candidate.id,
                summary=passport.summary,
                work_experience=passport.work_history,
                education=passport.education,
                certifications=passport.certifications,
                created_by=request.user.id,
            )

        return success_response(
            data={
                'candidate_id': str(candidate.id),
                'import_status': 'created' if created else 'already_exists',
            },
            message="Passport imported successfully."
        )
