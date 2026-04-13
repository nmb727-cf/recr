from dataclasses import dataclass
from django.db.models import Q


FORBIDDEN_SCOPE_PARAMS_DEFAULT = (
    'tenant_id',
    'company_tenant_id',
    'agency_tenant_id',
)
MASTER_ADMIN_PERMISSION = 'master_admin.access'
COMPANY_ROLES = {'tenant_admin', 'hr_manager', 'hiring_manager', 'recruiter'}
AGENCY_ROLES = {'agency_owner', 'agency_admin', 'agency_recruiter'}


@dataclass
class ScopeCheckResult:
    ok: bool
    error_param: str | None = None


def is_platform_admin(user) -> bool:
    return can_access_master_admin(user)


def can_access_master_admin(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False

    if (
        getattr(user, 'role', '') == 'super_admin'
        or getattr(user, 'is_super_admin', False)
        or getattr(user, 'is_superuser', False)
        or getattr(user, 'is_staff', False)
    ):
        return True

    permissions = getattr(user, 'permissions', None)
    if isinstance(permissions, (list, tuple, set, frozenset)):
        return MASTER_ADMIN_PERMISSION in permissions

    # Fallback to RBAC lookup for normal request.user objects that do not expose
    # a permissions attribute directly.
    try:
        from apps.rbac.utils import get_user_permissions
        return MASTER_ADMIN_PERMISSION in get_user_permissions(user)
    except Exception:
        return False

    return False


def is_company_user(user) -> bool:
    return bool(getattr(user, 'role', '') in COMPANY_ROLES)


def is_agency_user(user) -> bool:
    return bool(getattr(user, 'role', '') in AGENCY_ROLES)


def validate_no_scope_widening_params(query_params, forbidden_params=FORBIDDEN_SCOPE_PARAMS_DEFAULT) -> ScopeCheckResult:
    for key in forbidden_params:
        if key in query_params:
            return ScopeCheckResult(ok=False, error_param=key)
    return ScopeCheckResult(ok=True)


def scope_queryset_by_tenant_fields(qs, *, user, tenant_fields=('tenant_id',), allow_platform_admin=False):
    """Apply safe tenant scoping over one or more tenant fields.

    If allow_platform_admin=True, platform admins can access unscoped queryset.
    Otherwise access is always constrained to the user's tenant_id.
    """
    if allow_platform_admin and is_platform_admin(user):
        return qs

    tenant_id = getattr(user, 'tenant_id', None)
    if not tenant_id:
        return qs.none()

    predicate = Q()
    for field in tenant_fields:
        predicate |= Q(**{field: tenant_id})
    return qs.filter(predicate)


def scope_candidate_visibility_qs(*, candidate_qs, user, application_model, engagement_model):
    """Global candidate-safe visibility rule.

    Candidate core identity is global, but tenant-facing visibility is restricted to:
    - candidates whose tenant_id equals request tenant
    - candidates associated to tenant via applications
    - candidates associated to tenant via engagements
    """
    if is_platform_admin(user):
        return candidate_qs

    tenant_id = getattr(user, 'tenant_id', None)
    if not tenant_id:
        return candidate_qs.none()

    visible_from_apps = application_model.objects.filter(
        tenant_id=tenant_id,
        is_deleted=False,
    ).values('candidate_id')

    visible_from_engagements = engagement_model.objects.filter(
        tenant_id=tenant_id,
        is_deleted=False,
    ).values('candidate_id')

    return candidate_qs.filter(
        Q(tenant_id=tenant_id) |
        Q(id__in=visible_from_apps) |
        Q(id__in=visible_from_engagements)
    )


def scope_agency_relationship_qs(*, relationship_qs, user, allow_platform_admin=True):
    if allow_platform_admin and is_platform_admin(user):
        return relationship_qs

    tenant_id = getattr(user, 'tenant_id', None)
    if not tenant_id:
        return relationship_qs.none()

    return relationship_qs.filter(
        Q(company_tenant_id=tenant_id) | Q(agency_tenant_id=tenant_id)
    )


class TenantAccessMixin:
    """Reusable mixin for tenant-safe API view access patterns."""

    def reject_scope_widening(self, request, forbidden_params=FORBIDDEN_SCOPE_PARAMS_DEFAULT):
        result = validate_no_scope_widening_params(request.query_params, forbidden_params=forbidden_params)
        if not result.ok:
            from apps.core.responses import error_response
            return error_response(
                f"Scope widening via '{result.error_param}' is not allowed.",
                status_code=400,
            )
        return None

    def tenant_scope(self, qs, *, request, tenant_fields=('tenant_id',), allow_platform_admin=False):
        return scope_queryset_by_tenant_fields(
            qs,
            user=request.user,
            tenant_fields=tenant_fields,
            allow_platform_admin=allow_platform_admin,
        )

    def relationship_scope(self, qs, *, request, allow_platform_admin=True):
        return scope_agency_relationship_qs(
            relationship_qs=qs,
            user=request.user,
            allow_platform_admin=allow_platform_admin,
        )
