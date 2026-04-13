from rest_framework.permissions import BasePermission


class CanManagePrequalForms(BasePermission):
    """Allow tenant admins, recruiters, and hiring managers to manage forms."""

    ALLOWED_ROLES = {'tenant_admin', 'super_admin', 'recruiter', 'hiring_manager'}

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'role', None) in self.ALLOWED_ROLES


class CanViewPrequalForms(BasePermission):
    """Allow any authenticated company-side user to view forms."""

    ALLOWED_ROLES = {
        'tenant_admin', 'super_admin', 'recruiter',
        'hiring_manager', 'agency_owner', 'agency_admin', 'agency_recruiter',
    }

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'role', None) in self.ALLOWED_ROLES
