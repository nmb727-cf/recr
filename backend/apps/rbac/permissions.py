"""
DRF permission classes for RBAC.

────────────────────────────────────────────────────────────────────────────────
Usage
────────────────────────────────────────────────────────────────────────────────

  from apps.rbac.permissions import require_permission

  class CandidateListView(APIView):
      permission_classes = [IsAuthenticated, require_permission('candidates.candidate.view')]

  # Require ALL of multiple permissions:
  class CandidateCreateView(APIView):
      permission_classes = [
          IsAuthenticated,
          require_permission('candidates.candidate.view', 'candidates.candidate.create'),
      ]

────────────────────────────────────────────────────────────────────────────────
Design note
────────────────────────────────────────────────────────────────────────────────
DRF instantiates permission classes without constructor arguments, so we use a
factory function that dynamically generates a class with the required codes
baked in as a class attribute.  This avoids the need for per-permission
subclasses while keeping the standard DRF permission_classes interface.
"""
from rest_framework.permissions import BasePermission
from apps.rbac.utils import user_has_all_permissions


def require_permission(*permission_codes: str):
    """
    Factory: returns a DRF BasePermission subclass that checks all given codes.

    Args:
        *permission_codes: one or more permission codes that the user must hold.

    Returns:
        A BasePermission subclass ready to use in permission_classes.
    """
    codes = permission_codes  # capture in closure

    class _RequirePermission(BasePermission):
        _codes = codes
        message = f'You do not have the required permission(s): {", ".join(codes)}'

        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            return user_has_all_permissions(request.user, *self._codes)

    # Give the dynamic class a readable name for debugging/logging
    _RequirePermission.__name__ = f'RequirePermission({", ".join(codes)})'
    _RequirePermission.__qualname__ = _RequirePermission.__name__

    return _RequirePermission
