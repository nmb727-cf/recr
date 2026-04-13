"""
Candidate Identity Resolver
===========================
Centralised identity lifecycle service used by:

  Source 1 — company/agency candidate add flows
  Source 2 — invite/apply-link submissions
  Source 3 — direct candidate signup
  Passport sync/import flows
  Job application candidate resolution

Core goals:
  1) Resolve one canonical candidate identity by strong signals only
  2) Link user accounts without creating shadow candidate rows
  3) Attach tenant associations explicitly for multi-tenant visibility
  4) Keep duplicate handling conservative and auditable
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db.models import Q
from django.utils import timezone


MASTER_CANDIDATE_SOURCE = "identity_resolver"


@dataclass
class CandidateResolutionResult:
    candidate: Any | None
    created: bool
    matched_on: str
    user_linked: bool
    tenant_associated: bool
    tenant_association_created: bool


def _norm_email(email: str = "") -> str:
    return (email or "").strip().lower()


def _norm_phone(phone: str = "") -> str:
    return (phone or "").strip()


def _phone_variants(phone: str = "") -> set[str]:
    raw = _norm_phone(phone)
    if not raw:
        return set()
    digits = "".join(ch for ch in raw if ch.isdigit())
    variants = {raw}
    if digits:
        variants.add(digits)
        variants.add(f"+{digits}")
    return {v for v in variants if v}


def _emit_candidate_timeline_event(*, tenant_id, candidate_id, event_type: str, payload: dict, source: str = "system") -> None:
    if not tenant_id:
        return
    try:
        from apps.candidates.models import CandidateTimelineEvent

        CandidateTimelineEvent.objects.create(
            tenant_id=tenant_id,
            candidate_id=candidate_id,
            event_type=event_type,
            payload=payload or {},
            source=source,
        )
    except Exception:
        # Lifecycle events must never block identity operations.
        pass


def _emit_candidate_domain_event(name: str, **kwargs) -> None:
    try:
        from apps.core import events
        signal = getattr(events.candidate, name, None)
        if signal is not None:
            signal.send(sender=events.candidate.__class__, **kwargs)
    except Exception:
        pass


def match_candidate(email: str = "", phone: str = ""):
    """
    Resolve candidate by conservative identity keys only:
      1) email + phone
      2) email
      3) phone
    """
    from apps.candidates.models import Candidate

    email = _norm_email(email)
    phone_variants = _phone_variants(phone)

    if not email and not phone_variants:
        return None

    if email and phone_variants:
        match = Candidate.objects.filter(
            email__iexact=email,
            is_deleted=False,
        ).filter(
            Q(phone__in=phone_variants) | Q(phone_number__in=phone_variants)
        ).first()
        if match:
            return match

    if email:
        match = Candidate.objects.filter(
            email__iexact=email,
            is_deleted=False,
        ).first()
        if match:
            return match

    if phone_variants:
        match = Candidate.objects.filter(
            Q(phone__in=phone_variants) | Q(phone_number__in=phone_variants),
            is_deleted=False,
        ).first()
        if match:
            return match

    return None


def match_user(email: str = "", phone: str = ""):
    from apps.accounts.models import CustomUser

    email = _norm_email(email)
    phone_variants = _phone_variants(phone)

    if not email and not phone_variants:
        return None

    if email and phone_variants:
        match = CustomUser.objects.filter(email__iexact=email).filter(
            Q(phone__in=phone_variants) | Q(phone_number__in=phone_variants)
        ).first()
        if match:
            return match

    if email:
        match = CustomUser.objects.filter(email__iexact=email).first()
        if match:
            return match

    if phone_variants:
        match = CustomUser.objects.filter(
            Q(phone__in=phone_variants) | Q(phone_number__in=phone_variants)
        ).first()
        if match:
            return match

    return None


def ensure_candidate_profile(candidate, *, tenant_id=None, created_by=None):
    from apps.candidates.models import CandidateProfile

    defaults = {}
    if tenant_id:
        defaults["tenant_id"] = tenant_id
    if created_by:
        defaults["created_by"] = created_by
    profile, created = CandidateProfile.objects.get_or_create(
        candidate_id=candidate.id,
        defaults=defaults,
    )
    return profile, created


def link_user_to_candidate(user, candidate):
    """
    Explicitly links a user account to a candidate.
    Returns False if candidate is already linked to a different user.
    """
    if candidate.user_id and str(candidate.user_id) != str(user.id):
        return False

    update_fields = []
    if str(candidate.user_id or "") != str(user.id):
        candidate.user_id = user.id
        update_fields.append("user_id")
    if candidate.account_status != "claimed":
        candidate.account_status = "claimed"
        update_fields.append("account_status")
    if not candidate.claimed_at:
        candidate.claimed_at = timezone.now()
        update_fields.append("claimed_at")

    if update_fields:
        update_fields.append("updated_at")
        candidate.save(update_fields=update_fields)
        _emit_candidate_timeline_event(
            tenant_id=candidate.owner_tenant_id or candidate.tenant_id,
            candidate_id=candidate.id,
            event_type="candidate.linked_to_user",
            payload={
                "user_id": str(user.id),
            },
            source="system",
        )
        _emit_candidate_domain_event(
            "linked_to_user",
            candidate_id=candidate.id,
            user_id=user.id,
        )
    return True


def ensure_tenant_association(
    candidate,
    *,
    tenant_id,
    source_tenant_id=None,
    actor_user_id=None,
    reason="identity_resolver",
    ensure_visibility=False,
) -> tuple[bool, bool]:
    """
    Creates/ensures an explicit multi-tenant association.

    Association is represented through CandidateTenantRight in `shared` mode.
    This keeps candidate identity global while preserving tenant visibility.
    """
    from apps.candidates.models import CandidateEngagement, CandidateTenantRight

    if not tenant_id:
        return False, False

    source_tid = source_tenant_id or tenant_id

    right = CandidateTenantRight.objects.filter(
        candidate_id=candidate.id,
        source_tenant_id=source_tid,
        target_tenant_id=tenant_id,
        relationship_type="shared",
        is_deleted=False,
    ).first()
    created_right = False
    if not right:
        right = CandidateTenantRight.objects.create(
            tenant_id=tenant_id,
            candidate_id=candidate.id,
            source_tenant_id=source_tid,
            target_tenant_id=tenant_id,
            relationship_type="shared",
            status="active_shared",
            retention_scope="global_identity",
            retention_post_expiry="shared",
            created_by=actor_user_id,
            metadata={"reason": reason},
        )
        created_right = True

    visibility_created = False
    if ensure_visibility:
        engagement = CandidateEngagement.objects.filter(
            tenant_id=tenant_id,
            candidate_id=candidate.id,
            job__isnull=True,
            is_active=True,
            is_deleted=False,
        ).first()
        if not engagement:
            CandidateEngagement.objects.create(
                tenant_id=tenant_id,
                candidate_id=candidate.id,
                engagement_type="sourced",
                stage="new_lead",
                priority="warm",
                is_active=True,
                owner_user_id=actor_user_id,
                created_by_id=actor_user_id,
                last_activity_at=timezone.now(),
                metadata={"identity_association": True, "reason": reason},
            )
            visibility_created = True

    if created_right:
        _emit_candidate_timeline_event(
            tenant_id=tenant_id,
            candidate_id=candidate.id,
            event_type="candidate.associated_with_tenant",
            payload={
                "tenant_id": str(tenant_id),
                "source_tenant_id": str(source_tid),
                "reason": reason,
            },
            source="system",
        )
        _emit_candidate_domain_event(
            "associated_with_tenant",
            candidate_id=candidate.id,
            tenant_id=tenant_id,
            source_tenant_id=source_tid,
        )

    return True, created_right or visibility_created


def merge_candidate_payload(candidate, payload: dict, *, overwrite=False) -> list[str]:
    """
    Merge payload into an existing candidate conservatively.
    - overwrite=False: fill blanks only, union list fields
    - overwrite=True: explicit overwrite
    """
    if not payload:
        return []

    protected_fields = {
        "id",
        "candidate_ref_id",
        "tenant_id",
        "created_at",
        "updated_at",
        "created_by",
        "user_id",
        "duplicate_of",
        "is_duplicate",
        "global_hash",
    }
    list_union_fields = {"skills", "languages", "tags", "preferred_locations"}

    changed = []
    model_fields = {f.name for f in candidate._meta.fields}

    for key, incoming in payload.items():
        if key in protected_fields or key not in model_fields:
            continue

        if incoming is None:
            continue
        if isinstance(incoming, str) and incoming.strip() == "":
            continue

        existing = getattr(candidate, key, None)
        if key in list_union_fields and isinstance(incoming, list):
            existing_list = existing or []
            if overwrite:
                new_val = incoming
            else:
                existing_norm = {str(x).strip().lower() for x in existing_list}
                new_val = list(existing_list)
                for item in incoming:
                    norm = str(item).strip().lower()
                    if norm and norm not in existing_norm:
                        new_val.append(item)
                        existing_norm.add(norm)
            if new_val != existing_list:
                setattr(candidate, key, new_val)
                changed.append(key)
            continue

        if overwrite:
            if incoming != existing:
                setattr(candidate, key, incoming)
                changed.append(key)
            continue

        # Fill blank fields only
        is_blank = existing is None or existing == "" or existing == []
        if is_blank:
            setattr(candidate, key, incoming)
            changed.append(key)

    if changed:
        changed.append("updated_at")
        candidate.save(update_fields=changed)
    return changed


def resolve_candidate_identity(
    *,
    email: str = "",
    phone: str = "",
    user=None,
    passport_id=None,
    tenant_id=None,
    candidate_defaults: dict | None = None,
    create_if_missing=False,
    allow_cross_tenant=True,
    actor_user_id=None,
    ensure_tenant_association_flag=False,
    ensure_visibility=False,
    create_profile=True,
    source=MASTER_CANDIDATE_SOURCE,
) -> CandidateResolutionResult:
    from apps.candidates.models import Candidate

    email = _norm_email(email or (user.email if user else ""))
    phone = _norm_phone(phone or (getattr(user, "phone", "") if user else ""))

    candidate = None
    matched_on = "none"
    created = False
    user_linked = False
    tenant_associated = False
    tenant_association_created = False

    # Priority 0: explicit user link
    if user:
        candidate = Candidate.objects.filter(user_id=user.id, is_deleted=False).first()
        if candidate:
            matched_on = "user_id"

    # Priority 0.5: explicit passport link
    if not candidate and passport_id:
        qs = Candidate.objects.filter(passport_id=passport_id, is_deleted=False)
        if not allow_cross_tenant and tenant_id:
            qs = qs.filter(Q(tenant_id=tenant_id) | Q(owner_tenant_id=tenant_id))
        candidate = qs.first()
        if candidate:
            matched_on = "passport_id"

    # Priority 1..3: identity match
    if not candidate:
        candidate = match_candidate(email=email, phone=phone)
        if candidate:
            if not allow_cross_tenant and tenant_id and candidate.tenant_id and str(candidate.tenant_id) != str(tenant_id):
                candidate = None
            else:
                if email and _norm_email(candidate.email) == email and phone and _phone_variants(candidate.phone) & _phone_variants(phone):
                    matched_on = "email_phone"
                elif email and _norm_email(candidate.email) == email:
                    matched_on = "email"
                else:
                    matched_on = "phone"

    if not candidate and create_if_missing:
        defaults = dict(candidate_defaults or {})
        if user:
            defaults.setdefault("first_name", getattr(user, "first_name", "") or "")
            defaults.setdefault("last_name", getattr(user, "last_name", "") or "")
            defaults.setdefault("email", email)
            defaults.setdefault("phone", phone)
            defaults.setdefault("user_id", user.id)
            if defaults.get("account_status") in (None, "", "none"):
                defaults["account_status"] = "active"
        else:
            defaults.setdefault("email", email)
            defaults.setdefault("phone", phone)

        # Keep candidate self-signups global by default.
        if "tenant_id" not in defaults:
            is_candidate_user = bool(user and getattr(user, "role", "") == "candidate")
            defaults["tenant_id"] = None if is_candidate_user else tenant_id

        if tenant_id and not defaults.get("owner_tenant_id"):
            defaults["owner_tenant_id"] = tenant_id
        if actor_user_id and not defaults.get("created_by"):
            defaults["created_by"] = actor_user_id
        defaults.setdefault("source_type", "direct")
        defaults.setdefault("source", "self" if user and getattr(user, "role", "") == "candidate" else "company")
        defaults.setdefault("profile_status", "partial")
        defaults.setdefault("initial_entry_type", "self" if user and getattr(user, "role", "") == "candidate" else "manual")
        defaults.setdefault("candidate_state", "NEW_LEAD")
        defaults.setdefault("candidate_pool", "GENERAL")
        defaults.setdefault("is_general_pool_used", False)

        candidate = Candidate.objects.create(**defaults)
        matched_on = "created"
        created = True
        _emit_candidate_timeline_event(
            tenant_id=tenant_id or defaults.get("owner_tenant_id") or defaults.get("tenant_id"),
            candidate_id=candidate.id,
            event_type="candidate.created",
            payload={
                "source": source,
                "email": email,
                "tenant_id": str(tenant_id) if tenant_id else "",
            },
            source="system",
        )
        _emit_candidate_domain_event(
            "created",
            candidate_id=candidate.id,
            tenant_id=tenant_id,
            source=source,
        )

    if candidate and user and (not candidate.user_id or str(candidate.user_id) == str(user.id)):
        user_linked = link_user_to_candidate(user, candidate)

    if candidate and create_profile:
        ensure_candidate_profile(
            candidate,
            tenant_id=tenant_id or candidate.tenant_id or candidate.owner_tenant_id,
            created_by=actor_user_id,
        )

    if candidate and tenant_id and ensure_tenant_association_flag:
        tenant_associated, tenant_association_created = ensure_tenant_association(
            candidate,
            tenant_id=tenant_id,
            source_tenant_id=candidate.owner_tenant_id or tenant_id,
            actor_user_id=actor_user_id,
            reason=source,
            ensure_visibility=ensure_visibility,
        )

    return CandidateResolutionResult(
        candidate=candidate,
        created=created,
        matched_on=matched_on,
        user_linked=user_linked,
        tenant_associated=tenant_associated,
        tenant_association_created=tenant_association_created,
    )


def check_identity_status(email: str = "", phone: str = ""):
    candidate = match_candidate(email=email, phone=phone)
    user = match_user(email=email, phone=phone)

    return {
        "candidate_exists": candidate is not None,
        "user_exists": user is not None,
        "candidate_id": str(candidate.id) if candidate else None,
        "account_status": candidate.account_status if candidate else None,
    }
