"""
Candidate Claim Flow Views
===========================
These views power the /candidate/claim/<token> route — the page a candidate
visits when they follow a personalised link sent after a recruiter adds them
(Source 1) or embedded in an apply-link form confirmation (Source 2).

Flow:
  GET  /api/v1/candidates/claim/<token>/
       → Validates the token; returns prefilled identity data (name, email,
         phone) so the frontend can prepopulate the signup / login form.
         Does NOT require authentication.

  POST /api/v1/candidates/claim/<token>/
       → Called after the candidate has authenticated (signed up or logged in).
         Links their user account to the existing candidate record and marks
         the record as claimed.  Requires a valid JWT (IsAuthenticated).

Identity check endpoint:
  POST /api/v1/candidates/check-identity/
       → Public endpoint.  Accepts { email, phone } and returns whether a
         user account and/or candidate record already exist so the frontend
         can route to login / forgot-password instead of showing the signup form.
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers as drf_serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from apps.candidates.models import Candidate
from apps.candidates.identity_service import (
    link_user_to_candidate,
    check_identity_status,
)
from apps.core.responses import success_response, error_response


class CandidateClaimVerifyView(APIView):
    """
    Source 1 / Source 2 — Claim token verification.

    GET: Confirm the token is valid and unexpired; return prefilled data the
         frontend needs to populate the signup form.
    POST: Authenticated candidate submits after signup/login; link account.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Claim token is valid"),
            404: OpenApiResponse(description="Invalid or expired claim link"),
        }
    )
    def get(self, request, token):
        """
        Validate claim token and return prefilled candidate identity data.
        No authentication required — the candidate may not have an account yet.
        """
        try:
            candidate = Candidate.objects.get(
                claim_token=token,
                is_deleted=False,
            )
        except Candidate.DoesNotExist:
            return error_response("Invalid or expired claim link.", status_code=404)

        if (
            candidate.claim_token_expires_at
            and candidate.claim_token_expires_at < timezone.now()
        ):
            return error_response(
                "This claim link has expired. Please contact the recruiter for a new one.",
                status_code=410,
            )

        # Return just enough identity context for the frontend to prefill the form.
        # Do NOT expose sensitive internal fields.
        return success_response(data={
            'candidate': {
                'first_name': candidate.first_name,
                'last_name': candidate.last_name,
                'email': candidate.email,
                'phone': candidate.phone,
                'current_title': candidate.current_title,
                'current_company': candidate.current_company,
                'account_status': candidate.account_status,
                'already_claimed': candidate.account_status in ('claimed', 'active'),
            }
        }, message="Claim token is valid.")

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Profile successfully claimed"),
            401: OpenApiResponse(description="Authentication required to claim profile"),
            404: OpenApiResponse(description="Invalid claim token"),
        }
    )
    def post(self, request, token):
        """
        Link the authenticated user to the candidate record identified by token.
        Must be called after the candidate has signed up or logged in.
        Requires: Authorization header with a valid JWT.
        """
        # Require auth for the link step
        if not request.user or not request.user.is_authenticated:
            return error_response(
                "You must be signed in to claim this profile.", status_code=401
            )

        try:
            candidate = Candidate.objects.get(
                claim_token=token,
                is_deleted=False,
            )
        except Candidate.DoesNotExist:
            return error_response("Invalid claim token.", status_code=404)

        if (
            candidate.claim_token_expires_at
            and candidate.claim_token_expires_at < timezone.now()
        ):
            return error_response("This claim link has expired.", status_code=410)

        # Identity safety check: the authenticated user's email/phone must match
        # the candidate's email/phone to prevent account hijacking.
        user = request.user
        email_match = (
            user.email
            and candidate.email
            and user.email.lower() == candidate.email.lower()
        )
        phone_match = (
            (user.phone or user.phone_number)
            and (candidate.phone or candidate.phone_number)
            and (
                (user.phone and user.phone == candidate.phone)
                or (user.phone_number and user.phone_number == candidate.phone_number)
            )
        )

        if not email_match and not phone_match:
            return error_response(
                "Your account details do not match this profile. "
                "Please sign in with the email or phone this link was sent to.",
                status_code=403,
            )

        linked = link_user_to_candidate(user, candidate)
        if not linked:
            # Already claimed by a different user — treat as success so we
            # don't leak which account owns the record.
            return success_response(
                data={'already_claimed': True},
                message="This profile has already been claimed.",
            )

        return success_response(
            data={
                'candidate_id': str(candidate.id),
                'account_status': candidate.account_status,
            },
            message="Profile successfully claimed. Welcome!",
        )


class CandidateIdentityCheckView(APIView):
    """
    Public pre-check used by Source 2 (apply form) and Source 3 (direct signup)
    before creating a new user account.

    POST { email, phone } → returns whether a user/candidate already exists so
    the frontend can redirect to login / forgot-password instead of proceeding
    with account creation and creating a duplicate.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=inline_serializer(
            name='CandidateIdentityCheckRequest',
            fields={
                'email': drf_serializers.CharField(required=False, allow_blank=True),
                'phone': drf_serializers.CharField(required=False, allow_blank=True),
            },
        ),
        responses={
            200: OpenApiResponse(description="Identity check complete"),
            400: OpenApiResponse(description="Provide at least an email or phone to check"),
        }
    )
    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        email = data.get('email', '')
        phone = data.get('phone', '')
        # Reject non-string values (e.g. arrays sent as JSON)
        if not isinstance(email, str):
            email = ''
        if not isinstance(phone, str):
            phone = ''
        email = email.strip()
        phone = phone.strip()

        if not email and not phone:
            return success_response(
                data={'user_exists': False, 'candidate_exists': False, 'candidate_id': None, 'account_status': None},
                message="Identity check complete.",
            )

        result = check_identity_status(email=email, phone=phone)
        return success_response(data=result, message="Identity check complete.")
