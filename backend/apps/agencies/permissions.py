from rest_framework.permissions import BasePermission


class AgencyPerformancePermission(BasePermission):
    """Access control for agency performance endpoint.

    - Company users can view performance for agencies linked to their company tenant.
    - Agency users can view only their own agency performance.
    - Platform admins (staff/super_admin) can view broader data.
    """

    COMPANY_ROLES = {'tenant_admin', 'hr_manager', 'hiring_manager', 'recruiter'}
    AGENCY_ROLES = {'agency_owner', 'agency_admin', 'agency_recruiter'}

    def has_permission(self, request, view):
        user = request.user
        if not getattr(user, 'is_authenticated', False):
            return False
        if getattr(user, 'is_staff', False) or getattr(user, 'role', '') == 'super_admin':
            return True
        if getattr(user, 'role', '') in self.COMPANY_ROLES:
            return True
        if getattr(user, 'role', '') in self.AGENCY_ROLES:
            return True
        return False
