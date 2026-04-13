from rest_framework.permissions import BasePermission

ROLE_ADMIN   = {'super_admin', 'tenant_admin'}
ROLE_MANAGER = {'super_admin', 'tenant_admin', 'hr_manager'}
ROLE_VIEW    = {'super_admin', 'tenant_admin', 'hr_manager', 'recruiter', 'hiring_manager', 'viewer'}


def _role(roles):
    class RolePermission(BasePermission):
        _roles = roles
        message = f'You need one of these roles: {", ".join(sorted(roles))}'

        def has_permission(self, request, view):
            return bool(
                request.user
                and request.user.is_authenticated
                and getattr(request.user, 'role', None) in self._roles
            )
    return RolePermission


CanView   = _role(ROLE_VIEW)
CanManage = _role(ROLE_MANAGER)
CanAdmin  = _role(ROLE_ADMIN)
