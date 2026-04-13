"""
Custom drf-spectacular AutoSchema with global response injections:

  401  — injected for any view using IsAuthenticated / IsAdminUser.
  404  — injected for any endpoint whose URL contains path parameters
         (e.g. {pk}, {id}, {uuid}) since those always risk a missing-resource
         response that Schemathesis will probe.

These two rules eliminate ~249 Schemathesis "Undocumented HTTP status code"
failures without touching individual views.
"""
from drf_spectacular.openapi import AutoSchema as _BaseAutoSchema
from drf_spectacular.utils import OpenApiResponse
from rest_framework.permissions import IsAuthenticated, IsAdminUser


_AUTH_PERMISSION_CLASSES = (IsAuthenticated, IsAdminUser)

_401_RESPONSE = OpenApiResponse(
    description="Authentication credentials were not provided or are invalid.",
)
_404_RESPONSE = OpenApiResponse(
    description="Resource not found.",
)


class TalentOSAutoSchema(_BaseAutoSchema):
    """
    Extends drf-spectacular's AutoSchema with two automatic response injections.
    """

    def _view_requires_auth(self) -> bool:
        """Return True if this view enforces authentication."""
        try:
            permissions = self.view.get_permissions()
        except Exception:
            return False
        return any(isinstance(p, _AUTH_PERMISSION_CLASSES) for p in permissions)

    def _path_has_parameters(self) -> bool:
        """Return True if the URL path contains any path parameters."""
        return '{' in self.path

    def _get_response_bodies(self, direction='response'):
        responses = super()._get_response_bodies(direction=direction)
        if self._view_requires_auth() and '401' not in responses:
            responses['401'] = self._get_response_for_code(
                _401_RESPONSE, '401', direction=direction
            )
        if '404' not in responses:
            responses['404'] = self._get_response_for_code(
                _404_RESPONSE, '404', direction=direction
            )
        return responses
