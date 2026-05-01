from rest_framework.permissions import BasePermission

EXECUTIVE_ROLES = {'super_admin', 'tenant_admin'}
MANAGER_ROLES   = {'super_admin', 'tenant_admin', 'hr_manager'}


def _role(allowed: set):
    class _P(BasePermission):
        def has_permission(self, request, view):
            role = getattr(request.user, 'role', None)
            return bool(request.user and request.user.is_authenticated and role in allowed)
    return _P


ExecutiveReadPermission   = _role(EXECUTIVE_ROLES | {'hr_manager', 'recruiter', 'hiring_manager'})
ExecutiveWritePermission  = _role(MANAGER_ROLES)
ExecutiveAdminPermission  = _role(EXECUTIVE_ROLES)
