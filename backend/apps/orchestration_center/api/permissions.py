from rest_framework.permissions import BasePermission


PERMISSION_ROLE_MAP = {
    'overview.view': {'super_admin', 'tenant_admin', 'hr_manager', 'recruiter', 'hiring_manager', 'viewer'},
    'providers.view': {'super_admin', 'tenant_admin', 'viewer'},
    'providers.manage': {'super_admin', 'tenant_admin'},
    'prompts.view': {'super_admin', 'tenant_admin', 'hr_manager', 'viewer'},
    'prompts.manage': {'super_admin', 'tenant_admin'},
    'prompts.approve': {'super_admin', 'tenant_admin'},
    'automations.view': {'super_admin', 'tenant_admin', 'hr_manager', 'recruiter', 'hiring_manager', 'viewer'},
    'automations.manage': {'super_admin', 'tenant_admin'},
    'suggestions.view': {'super_admin', 'tenant_admin', 'hr_manager', 'recruiter', 'hiring_manager', 'viewer'},
    'suggestions.manage': {'super_admin', 'tenant_admin', 'hr_manager', 'recruiter', 'hiring_manager'},
    'executions.view': {'super_admin', 'tenant_admin', 'hr_manager', 'recruiter', 'hiring_manager', 'viewer'},
    'executions.manage': {'super_admin', 'tenant_admin', 'hr_manager', 'recruiter', 'hiring_manager'},
    'failures.view': {'super_admin', 'tenant_admin', 'hr_manager', 'viewer'},
    'failures.manage': {'super_admin', 'tenant_admin', 'hr_manager'},
    'approvals.view': {'super_admin', 'tenant_admin', 'hr_manager', 'viewer'},
    'approvals.manage': {'super_admin', 'tenant_admin', 'hr_manager'},
    'connectors.view': {'super_admin', 'tenant_admin', 'hr_manager', 'viewer'},
    'settings.manage': {'super_admin', 'tenant_admin'},
}


def require_roles(*roles):
    class RolePermission(BasePermission):
        message = f'You need one of these roles: {", ".join(roles)}'

        def has_permission(self, request, view):
            return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) in roles)

    return RolePermission


def require_hub_permission(permission_key: str):
    allowed_roles = tuple(sorted(PERMISSION_ROLE_MAP.get(permission_key, set())))
    return require_roles(*allowed_roles)
