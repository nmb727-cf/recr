from rest_framework.permissions import BasePermission
from shared.tenant_access import can_access_master_admin


class IsSuperAdmin(BasePermission):
    message = "Master admin access is restricted to super admins."

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        return can_access_master_admin(user)
