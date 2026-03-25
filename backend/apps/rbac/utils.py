"""
Runtime permission resolution utilities.

Usage in views:
    from apps.rbac.utils import user_has_permission, get_user_permissions

    # Boolean check
    if user_has_permission(request.user, 'candidates.candidate.view'):
        ...

    # Bulk: get all permission codes for a user
    perms = get_user_permissions(request.user)   # returns frozenset[str]

Caching strategy (current):
    Results are cached in Django's default cache for 5 minutes per user.
    If Django's cache backend is the dummy (not configured), queries hit the
    DB each time — still fast with the indexed FK joins.

    Cache is invalidated automatically when seed_rbac is re-run (it deletes
    all keys matching the pattern used here).  For manual invalidation call:
        invalidate_user_permission_cache(user)
"""
from django.core.cache import cache
from django.db.models import Case, IntegerField, Q, Value, When


_CACHE_TTL = 300  # 5 minutes
_CACHE_KEY_PREFIX = 'rbac_perms'


def _cache_key(user) -> str:
    # Key includes role so a role change (which also changes user.role) naturally
    # busts the cache without an explicit invalidation call.
    return f'{_CACHE_KEY_PREFIX}:{user.pk}:{user.role}'


def get_user_permissions(user) -> frozenset:
    """
    Return the effective permission codes for *user* as a frozenset of strings.

    Returns an empty frozenset for anonymous / unauthenticated users.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return frozenset()

    key = _cache_key(user)
    cached = cache.get(key)
    if cached is not None:
        return cached

    from apps.rbac.models import Role, RolePermission

    role = (
        Role.objects
        .filter(name=user.role)
        .filter(Q(tenant_id=user.tenant_id) | Q(tenant_id__isnull=True))
        .annotate(
            _priority=Case(
                When(tenant_id=user.tenant_id, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by('_priority', '-updated_at')
        .first()
    )

    if role is None:
        cache.set(key, frozenset(), _CACHE_TTL)
        return frozenset()

    codes = frozenset(
        RolePermission.objects
        .filter(
            role=role,
            permission__is_active=True,
        )
        .values_list('permission__code', flat=True)
    )

    cache.set(key, codes, _CACHE_TTL)
    return codes


def user_has_permission(user, permission_code: str) -> bool:
    """Return True if *user* holds the given permission code."""
    return permission_code in get_user_permissions(user)


def user_has_any_permission(user, *permission_codes: str) -> bool:
    """Return True if *user* holds at least one of the given permission codes."""
    effective = get_user_permissions(user)
    return any(code in effective for code in permission_codes)


def user_has_all_permissions(user, *permission_codes: str) -> bool:
    """Return True if *user* holds every one of the given permission codes."""
    effective = get_user_permissions(user)
    return all(code in effective for code in permission_codes)


def invalidate_user_permission_cache(user) -> None:
    """Explicitly clear the cached permissions for a user."""
    cache.delete(_cache_key(user))
