"""
Source 2 — Shared Candidate Fill Link
=======================================
A recruiter/agency creates a shareable apply link (CandidateInviteLink).  A
candidate opens it, fills the form, and optionally creates an account.

Identity rules enforced here:
  • Before creating a new candidate or user, we check whether the submitted
    email/phone already belongs to an existing record.
  • If a matching *user* account exists → return needs_login=True so the
    frontend routes the candidate to the login / forgot-password screen instead
    of creating a duplicate account.
  • If a matching *candidate* record exists (but no user yet) → link the new
    submission to the existing candidate rather than creating a duplicate.
  • If nothing exists → create candidate + optional user account as before.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.candidates.models import CandidateInviteLink, CandidateFormSubmission
from apps.candidates.identity_service import (
    match_user,
    link_user_to_candidate,
    resolve_candidate_identity,
    merge_candidate_payload,
)
from apps.core.responses import success_response, error_response
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiResponse

class InviteLinkListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        links = CandidateInviteLink.objects.filter(
            tenant_id=request.user.tenant_id,
        ).order_by('-created_at')
        data = [{
            'id': str(l.id),
            'token': l.token,
            'url': f'/apply/{l.token}/',
            'job_id': str(l.job_id) if l.job_id else None,
            'status': l.status,
            'use_count': l.use_count,
            'max_uses': l.max_uses,
            'expires_at': l.expires_at,
            'created_at': l.created_at,
        } for l in links]
        return success_response(data={'links': data}, message="Invite links retrieved.")

    def post(self, request):
        import secrets
        from datetime import timedelta
        
        expires_days = request.data.get('expires_days')
        expires_at = None
        if expires_days:
            expires_at = timezone.now() + timedelta(days=int(expires_days))

        link = CandidateInviteLink.objects.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            token=secrets.token_urlsafe(32),
            job_id=request.data.get('job_id'),
            form_config=request.data.get('form_config', {}),
            expires_at=expires_at,
            max_uses=request.data.get('max_uses'),
        )
        return success_response(
            data={
                'link': {
                    'id': str(link.id),
                    'token': link.token,
                    'url': f'/apply/{link.token}/',
                    'expires_at': link.expires_at,
                }
            },
            message="Invite link created.",
            status_code=201
        )


class InviteLinkDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            link = CandidateInviteLink.objects.get(
                id=pk, tenant_id=request.user.tenant_id
            )
        except CandidateInviteLink.DoesNotExist:
            return error_response("Link not found.", status_code=404)
        link.status = 'disabled'
        link.save()
        return success_response(message="Link deactivated.")

@extend_schema(
    responses={
        200: OpenApiResponse(description="Success"),
        404: OpenApiResponse(description="Invalid or expired link."),
    }
)
class PublicApplyFormView(APIView):
    permission_classes = [AllowAny]

    def _rate_limit_exceeded(self, request, token):
        ip_addr = request.META.get('REMOTE_ADDR', '') or 'unknown'
        method = request.method.upper()
        ttl_seconds = int(getattr(settings, 'CANDIDATE_PUBLIC_APPLY_RATE_WINDOW_SECONDS', 60))
        if method == 'POST':
            limit = int(getattr(settings, 'CANDIDATE_PUBLIC_APPLY_POST_RATE_LIMIT', 20))
        else:
            limit = int(getattr(settings, 'CANDIDATE_PUBLIC_APPLY_GET_RATE_LIMIT', 60))
        key = f'candidate_public_apply:{method}:{token}:{ip_addr}'
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
            return error_response("Too many requests. Please retry shortly.", status_code=429)
        try:
            link = CandidateInviteLink.objects.get(
                token=token, status='active'
            )
        except CandidateInviteLink.DoesNotExist:
            return error_response("Invalid or expired link.", status_code=404)

        if link.expires_at and link.expires_at < timezone.now():
            return error_response("This invite link has expired.", status_code=410)

        if link.max_uses and link.use_count >= link.max_uses:
            return error_response("This invite link has reached its maximum uses.", status_code=410)

        from apps.tenants.models import Client
        try:
            tenant = Client.objects.get(id=link.tenant_id)
            company_name = tenant.name
        except:
            company_name = "A Company"

        job_title = None
        if link.job_id:
            from apps.jobs.models import JobRequisition
            try:
                job = JobRequisition.objects.get(id=link.job_id)
                job_title = job.title
            except:
                pass

        return success_response(data={
            'company_name': company_name,
            'job_title': job_title,
            'form_config': link.form_config,
        }, message="Form config retrieved.")

    def post(self, request, token):
        if self._rate_limit_exceeded(request, token):
            return error_response("Too many requests. Please retry shortly.", status_code=429)
        """
        Source 2 — Candidate submits the apply form.

        Identity deduplication:
          1. If a user account already exists with the submitted email/phone →
             return needs_login=True so the frontend shows the login screen.
          2. If a candidate record already exists (no user yet) → append the
             submission data but do NOT create a second candidate row.
          3. If neither exists → create candidate + optional user account.
        """
        try:
            link = CandidateInviteLink.objects.get(
                token=token, status='active'
            )
        except CandidateInviteLink.DoesNotExist:
            return error_response("Invalid or expired link.", status_code=404)

        if link.expires_at and link.expires_at < timezone.now():
            return error_response("This invite link has expired.", status_code=410)

        submitted_email = request.data.get('email', '').strip().lower()
        submitted_phone = request.data.get('phone', '').strip()

        # ── Identity check: does a user account already exist? ─────────────
        # If yes, do not create a duplicate account — tell the frontend to
        # redirect to login / forgot-password instead.
        existing_user = match_user(email=submitted_email, phone=submitted_phone)
        if existing_user and request.data.get('wants_account') and request.data.get('password'):
            return success_response(
                data={
                    'needs_login': True,
                    'email': existing_user.email,
                },
                message=(
                    "An account with this email or phone already exists. "
                    "Please log in to continue."
                ),
                status_code=200,
            )

        from apps.candidates.models import Candidate

        # Create the submission record first (always, for audit trail)
        submission = CandidateFormSubmission.objects.create(
            invite_link_id=link.id,
            tenant_id=link.tenant_id,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
            email=submitted_email,
            phone=submitted_phone,
            cv_filename=request.data.get('cv_filename', ''),
            form_data=request.data,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            wants_account=request.data.get('wants_account', False),
        )

        resolution = resolve_candidate_identity(
            email=submitted_email,
            phone=submitted_phone,
            tenant_id=link.tenant_id,
            create_if_missing=True,
            allow_cross_tenant=True,
            actor_user_id=link.created_by,
            ensure_tenant_association_flag=True,
            ensure_visibility=True,
            source='invite_apply',
            candidate_defaults={
                'tenant_id': link.tenant_id,
                'first_name': request.data.get('first_name', ''),
                'last_name': request.data.get('last_name', ''),
                'email': submitted_email,
                'phone': submitted_phone,
                'linkedin_url': request.data.get('linkedin_url', ''),
                'current_title': request.data.get('current_title', ''),
                'current_company': request.data.get('current_company', ''),
                'current_location_city': request.data.get('current_location_city', ''),
                'experience_years': request.data.get('experience_years'),
                'relevant_experience_years': request.data.get('relevant_experience_years'),
                'skills': request.data.get('skills', []),
                'nationality': request.data.get('nationality', ''),
                'work_authorization': request.data.get('work_authorization', 'not_specified'),
                'highest_education': request.data.get('highest_education', ''),
                'graduation_year': request.data.get('graduation_year'),
                'availability_status': request.data.get('availability_status', ''),
                'notice_period_days': request.data.get('notice_period_days'),
                'work_mode_preference': request.data.get('work_mode_preference', 'any'),
                'resume_url': request.data.get('resume_url', ''),
                'source': 'company',
                'source_type': 'direct',
                'source_detail': 'Invite apply link',
                'initial_entry_type': 'invite',
                'profile_status': 'partial',
                'owner_tenant_id': link.tenant_id,
                'candidate_state': 'NEW_LEAD',
                'candidate_pool': 'GENERAL',
                'is_general_pool_used': False,
            },
        )
        candidate = resolution.candidate
        if not resolution.created:
            merge_candidate_payload(
                candidate,
                {
                    'first_name': request.data.get('first_name', ''),
                    'last_name': request.data.get('last_name', ''),
                    'linkedin_url': request.data.get('linkedin_url', ''),
                    'current_title': request.data.get('current_title', ''),
                    'current_company': request.data.get('current_company', ''),
                    'current_location_city': request.data.get('current_location_city', ''),
                    'experience_years': request.data.get('experience_years'),
                    'relevant_experience_years': request.data.get('relevant_experience_years'),
                    'skills': request.data.get('skills', []),
                    'nationality': request.data.get('nationality', ''),
                    'work_authorization': request.data.get('work_authorization', 'not_specified'),
                    'highest_education': request.data.get('highest_education', ''),
                    'graduation_year': request.data.get('graduation_year'),
                    'availability_status': request.data.get('availability_status', ''),
                    'notice_period_days': request.data.get('notice_period_days'),
                    'work_mode_preference': request.data.get('work_mode_preference', 'any'),
                    'resume_url': request.data.get('resume_url', ''),
                },
                overwrite=False,
            )

        submission.candidate_id = candidate.id
        submission.status = 'processed'
        submission.save()

        # Increment use count
        link.use_count += 1
        link.save()

        # ── Optional account creation ──────────────────────────────────────
        # Only if candidate does not yet have a user account.
        access_token = None
        account_created = False
        if request.data.get('wants_account') and request.data.get('password'):
            from apps.accounts.models import CustomUser
            from apps.tenants.models import Client
            try:
                public_tenant = Client.objects.get(schema_name='public')
                # Re-check: existing_user may have been found above; if so skip.
                if not existing_user and not CustomUser.objects.filter(
                    email__iexact=submitted_email
                ).exists():
                    new_user = CustomUser.objects.create_user(
                        email=submitted_email,
                        password=request.data.get('password'),
                        first_name=request.data.get('first_name', ''),
                        last_name=request.data.get('last_name', ''),
                        role='candidate',
                        tenant_id=public_tenant.id,
                    )
                    # Link the new account to the candidate record immediately
                    link_user_to_candidate(new_user, candidate)

                    submission.user_id = new_user.id
                    submission.account_created = True
                    submission.status = 'converted'
                    submission.save()

                    from rest_framework_simplejwt.tokens import RefreshToken
                    refresh = RefreshToken.for_user(new_user)
                    access_token = str(refresh.access_token)
                    account_created = True
            except Exception:
                pass

        return success_response(
            data={
                'submission_id': str(submission.id),
                'candidate_id': str(candidate.id),
                'account_created': account_created,
                'needs_login': False,
                'access_token': access_token,
            },
            message="Application submitted successfully.",
            status_code=201,
        )


def _merge_submission_into_candidate(candidate, data: dict):
    """
    Append non-empty fields from a form submission into an existing candidate
    record.  Only fills in blank/null fields — never overwrites existing data.
    This preserves the recruiter's original data while enriching it with what
    the candidate submitted.
    """
    fields_to_merge = [
        'first_name', 'last_name', 'linkedin_url', 'current_title',
        'current_company', 'current_location_city', 'experience_years',
        'relevant_experience_years', 'nationality', 'work_authorization',
        'highest_education', 'graduation_year', 'availability_status',
        'notice_period_days', 'work_mode_preference', 'resume_url',
    ]
    changed = False
    for field in fields_to_merge:
        incoming = data.get(field)
        if incoming and not getattr(candidate, field, None):
            setattr(candidate, field, incoming)
            changed = True

    # Skills: merge lists (union), never overwrite
    incoming_skills = data.get('skills', [])
    if incoming_skills:
        existing = candidate.skills or []
        merged = list(dict.fromkeys(existing + incoming_skills))  # preserve order, deduplicate
        if merged != existing:
            candidate.skills = merged
            changed = True

    if changed:
        candidate.save()
