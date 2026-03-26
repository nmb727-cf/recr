"""
Candidate Identity Matching Service
====================================
Centralised utility used by all three candidate entry flows:

  Source 1 — Company/Agency adds a candidate manually (quick form / detailed form)
  Source 2 — Candidate opens a shared invite/apply link and fills the form
  Source 3 — Candidate signs up directly on the platform

The same logic is applied in every flow so the system never creates a duplicate
candidate or user record when the same email or phone is already on file.

Matching priority (strongest → weakest):
  1. email + phone  (both must match — highest confidence)
  2. email only     (case-insensitive)
  3. phone only     (exact match, normalised to digits)
"""

from django.db.models import Q


def match_candidate(email: str = '', phone: str = ''):
    """
    Return an existing Candidate whose identity matches the given email and/or
    phone.  Returns None if no match is found.

    Only non-deleted candidates are considered.  The caller decides what to do
    with the result (link, merge, redirect, etc.).
    """
    from apps.candidates.models import Candidate

    email = (email or '').strip().lower()
    phone = (phone or '').strip()

    if not email and not phone:
        return None

    # Priority 1: email + phone together
    if email and phone:
        match = Candidate.objects.filter(
            email__iexact=email,
            phone=phone,
            is_deleted=False,
        ).first()
        if match:
            return match

    # Priority 2: email alone
    if email:
        match = Candidate.objects.filter(
            email__iexact=email,
            is_deleted=False,
        ).first()
        if match:
            return match

    # Priority 3: phone alone
    if phone:
        match = Candidate.objects.filter(
            Q(phone=phone) | Q(phone_number=phone),
            is_deleted=False,
        ).first()
        if match:
            return match

    return None


def match_user(email: str = '', phone: str = ''):
    """
    Return an existing CustomUser whose identity matches the given email and/or
    phone.  Returns None if no match is found.

    Used before creating a new account to detect if a user already exists so
    we can route them to login / forgot-password instead.
    """
    from apps.accounts.models import CustomUser

    email = (email or '').strip().lower()
    phone = (phone or '').strip()

    if not email and not phone:
        return None

    # Priority 1: email + phone together
    if email and phone:
        match = CustomUser.objects.filter(
            email__iexact=email,
            phone=phone,
        ).first()
        if match:
            return match

    # Priority 2: email alone
    if email:
        match = CustomUser.objects.filter(email__iexact=email).first()
        if match:
            return match

    # Priority 3: phone alone
    if phone:
        match = CustomUser.objects.filter(
            Q(phone=phone) | Q(phone_number=phone),
        ).first()
        if match:
            return match

    return None


def link_user_to_candidate(user, candidate):
    """
    Attach a CustomUser account to an existing Candidate record and mark the
    candidate as claimed.

    This is called after a successful signup or login that matches a pending
    candidate record (e.g. after a claim-token flow or an apply-link flow).

    If the candidate is already linked to a different user, the existing link
    is preserved and this call is a no-op (returns False).
    """
    from django.utils import timezone

    # Guard: already linked to a different account
    if candidate.user_id and str(candidate.user_id) != str(user.id):
        return False

    candidate.user_id = user.id
    candidate.account_status = 'claimed'
    if not candidate.claimed_at:
        candidate.claimed_at = timezone.now()
    candidate.save(update_fields=['user_id', 'account_status', 'claimed_at', 'updated_at'])
    return True


def check_identity_status(email: str = '', phone: str = ''):
    """
    Return a dict summarising what already exists for the given identity.
    Used by frontend pre-checks so the UI can decide whether to show
    login / forgot-password / or continue with a new account.

    Returns:
      {
        'candidate_exists': bool,
        'user_exists': bool,
        'candidate_id': str | None,
        'account_status': str | None,  # none / invited / claimed / active
      }
    """
    candidate = match_candidate(email=email, phone=phone)
    user = match_user(email=email, phone=phone)

    return {
        'candidate_exists': candidate is not None,
        'user_exists': user is not None,
        'candidate_id': str(candidate.id) if candidate else None,
        'account_status': candidate.account_status if candidate else None,
    }
