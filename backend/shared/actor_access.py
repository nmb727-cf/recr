from rest_framework.exceptions import PermissionDenied

PLATFORM_ADMIN_ROLES = {'super_admin'}
TENANT_ADMIN_ROLES = {'tenant_admin'}
COMPANY_HIRING_ROLES = {'hr_manager', 'hiring_manager', 'recruiter'}
COMPANY_OPERATIONAL_ROLES = TENANT_ADMIN_ROLES | COMPANY_HIRING_ROLES
AGENCY_OPERATIONAL_ROLES = {'agency_owner', 'agency_admin', 'agency_recruiter'}
COMPANY_OR_AGENCY_OPERATIONAL_ROLES = COMPANY_OPERATIONAL_ROLES | AGENCY_OPERATIONAL_ROLES


def role_of(user) -> str:
    return getattr(user, 'role', '') or ''


def is_candidate(user) -> bool:
    return role_of(user) == 'candidate'


def is_tenant_or_platform_admin(user) -> bool:
    return bool(getattr(user, 'is_staff', False)) or role_of(user) in (PLATFORM_ADMIN_ROLES | TENANT_ADMIN_ROLES)


def is_company_operational_user(user) -> bool:
    return role_of(user) in COMPANY_OPERATIONAL_ROLES


def is_agency_operational_user(user) -> bool:
    return role_of(user) in AGENCY_OPERATIONAL_ROLES


def require_candidate(user, message: str = "This endpoint is available only for candidate users."):
    if not is_candidate(user):
        raise PermissionDenied(message)


def require_non_candidate(user, message: str):
    if is_candidate(user):
        raise PermissionDenied(message)


def require_tenant_or_platform_admin(
    user,
    message: str = "Admin access required for this operation.",
):
    if not is_tenant_or_platform_admin(user):
        raise PermissionDenied(message)
