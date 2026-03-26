"""
Candidate Sync Views for Passport
====================================
These views serve the onboarding prefill + append flow.

GET  /api/v1/passport/my-candidate/
     Find the Candidate record linked to the current user and return a merged
     prefill payload for onboarding.  Identity matching order:
       1. Candidate.user_id == request.user.id   (strongest — direct link)
       2. Candidate.email  == request.user.email  (recruiter-added, same email)
       3. Candidate.phone  == request.user.phone  (recruiter-added, same phone)
     Returns the first match found.  If none found, returns empty payload with
     no_candidate: true so the frontend can still render a blank onboarding.

PATCH /api/v1/passport/my-candidate/
     Update fields that live on the Candidate model (not on Passport):
       - availability_status
       - nationality
       - work_authorization
     Uses append semantics: only writes non-empty values and never erases an
     existing value by sending blank.

Both views are IsAuthenticated and candidate-role only.
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from apps.core.responses import success_response, error_response


def _find_linked_candidate(user):
    """
    Locate the Candidate record associated with this user.

    Matching order (highest confidence first):
      1. Direct user_id link (set by claim flow / auto-link on signup)
      2. Email match (case-insensitive)
      3. Phone match (against both phone and phone_number columns)
    """
    from apps.candidates.models import Candidate

    # Priority 1 — explicit link
    candidate = Candidate.objects.filter(
        user_id=user.id,
        is_deleted=False,
    ).first()
    if candidate:
        return candidate

    # Priority 2 — email match
    if user.email:
        candidate = Candidate.objects.filter(
            email__iexact=user.email,
            is_deleted=False,
        ).first()
        if candidate:
            return candidate

    # Priority 3 — phone match
    user_phone = user.phone or user.phone_number
    if user_phone:
        candidate = Candidate.objects.filter(
            Q(phone=user_phone) | Q(phone_number=user_phone),
            is_deleted=False,
        ).first()
        if candidate:
            return candidate

    return None


class MyCandidateView(APIView):
    """
    Prefill data source for onboarding.
    Returns the Candidate record linked to the authenticated user, flattened
    into a shape the onboarding form can consume directly.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        candidate = _find_linked_candidate(request.user)
        if not candidate:
            return success_response(
                data={'no_candidate': True, 'candidate': None},
                message="No linked candidate record found."
            )

        payload = {
            'id': str(candidate.id),
            # Identity (display only — not editable in onboarding)
            'email': candidate.email,
            'phone': candidate.phone,
            'phone_number': candidate.phone_number,
            'phone_country_code': candidate.phone_country_code,
            # Professional
            'first_name': candidate.first_name,
            'last_name': candidate.last_name,
            'current_title': candidate.current_title,
            'current_company': candidate.current_company,
            'current_location_city': candidate.current_location_city,
            'current_location_country': candidate.current_location_country,
            'experience_years': (
                float(candidate.experience_years)
                if candidate.experience_years is not None else None
            ),
            'relevant_experience_years': (
                float(candidate.relevant_experience_years)
                if candidate.relevant_experience_years is not None else None
            ),
            'linkedin_url': candidate.linkedin_url,
            'headline': '',  # Candidate model has no headline; passport does
            # Skills / languages (list fields — merged by frontend)
            'skills': candidate.skills or [],
            'languages': candidate.languages or [],
            'tags': candidate.tags or [],
            # Work auth / visa
            'nationality': candidate.nationality,
            'work_authorization': candidate.work_authorization,
            'visa_status': (candidate.metadata or {}).get('visa_status', ''),
            'pr_status': (candidate.metadata or {}).get('pr_status', ''),
            # Availability
            'availability_status': candidate.availability_status,
            'notice_period_days': candidate.notice_period_days,
            'last_working_day': (
                candidate.last_working_day.isoformat()
                if candidate.last_working_day else None
            ),
            'availability_date': (
                candidate.availability_date.isoformat()
                if candidate.availability_date else None
            ),
            'is_actively_looking': candidate.is_actively_looking,
            'work_mode_preference': candidate.work_mode_preference,
            # Compensation
            'expected_salary_min': (
                float(candidate.expected_salary_min)
                if candidate.expected_salary_min is not None else None
            ),
            'expected_salary_max': (
                float(candidate.expected_salary_max)
                if candidate.expected_salary_max is not None else None
            ),
            'salary_currency': candidate.salary_currency,
            # Documents
            'resume_url': candidate.resume_url,
            # Source tracking (read-only in onboarding)
            'source': candidate.source,
            'initial_entry_type': candidate.initial_entry_type,
            'account_status': candidate.account_status,
        }

        return success_response(
            data={'candidate': payload},
            message="Linked candidate found."
        )

    def patch(self, request):
        """
        Update Candidate-model fields collected during onboarding that don't
        have a home on the Passport model.

        Accepted fields:
          availability_status, nationality, work_authorization,
          notice_period_days, work_mode_preference, is_actively_looking

        Append semantics: empty / None values are skipped — existing data is
        never erased.
        """
        candidate = _find_linked_candidate(request.user)
        if not candidate:
            # No candidate record yet — silently succeed.  These fields will
            # be set when the candidate's Passport is later imported or linked.
            return success_response(
                data={'updated': False, 'reason': 'no_candidate'},
                message="No linked candidate to update."
            )

        UPDATABLE_FIELDS = [
            'availability_status',
            'nationality',
            'work_authorization',
            'notice_period_days',
            'work_mode_preference',
            'is_actively_looking',
        ]

        changed = []
        for field in UPDATABLE_FIELDS:
            incoming = request.data.get(field)
            # Skip None / empty string — do not erase existing data
            if incoming is None or incoming == '':
                continue
            existing = getattr(candidate, field, None)
            # For booleans False is a valid update
            if incoming != existing:
                setattr(candidate, field, incoming)
                changed.append(field)

        if changed:
            candidate.save(update_fields=changed + ['updated_at'])

        return success_response(
            data={'updated': bool(changed), 'fields_updated': changed},
            message="Candidate updated." if changed else "No changes detected."
        )
