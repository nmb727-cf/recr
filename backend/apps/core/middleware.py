"""
Core middleware for TalentOS API.
"""
from django.http import JsonResponse


# Standard HTTP methods for a REST API.
# Anything outside this set is rejected with 405 before reaching DRF.
_ALLOWED_METHODS = frozenset({
    'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS',
})

_drf_patched = False


def _patch_drf_dispatch():
    """
    Patch DRF's APIView.dispatch() to evaluate the method handler BEFORE
    running authentication (self.initial()).

    Root cause of "Unsupported methods" Schemathesis failures:
      DRF calls self.initial() (which runs IsAuthenticated / JWT auth) before
      checking whether the HTTP method is implemented on the view.  When
      Schemathesis sends an unsupported method (e.g. PUT to a GET-only view)
      with a malformed Authorization header, JWT raises AuthenticationFailed
      (401) before the method-not-allowed check can produce a 405.

    Fix: determine the handler first; if the method is not supported, return
    405 immediately without touching auth.  Supported methods proceed through
    the original flow unchanged.
    """
    global _drf_patched
    if _drf_patched:
        return

    from rest_framework.views import APIView

    def _dispatch(self, request, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers

        try:
            # ── Determine handler BEFORE auth ──────────────────────────────
            # Look up handler by method name; use None (not http_method_not_allowed)
            # as the sentinel so we avoid the bound-method identity trap —
            # `handler is self.http_method_not_allowed` is always False in Python
            # because bound methods are created fresh on each attribute access.
            method_lower = request.method.lower()
            if method_lower in self.http_method_names:
                handler = getattr(self, method_lower, None)
            else:
                handler = None

            if handler is None:
                # Method not supported by this view — skip auth, return 405.
                response = self.http_method_not_allowed(request, *args, **kwargs)
            else:
                # Method is supported — run normal DRF auth + handler flow.
                self.initial(request, *args, **kwargs)
                response = handler(request, *args, **kwargs)

        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response

    APIView.dispatch = _dispatch
    _drf_patched = True


class DisallowNonStandardMethodsMiddleware:
    """
    Two responsibilities:

    1. Returns 405 for HTTP methods outside the standard REST set
       (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS) — handles exotic
       methods like TRACE before they reach any DRF view.

    2. Applies the DRF dispatch patch (once, at server startup) so that
       view-level unsupported methods (e.g. PUT on a GET-only endpoint)
       also return 405 instead of 401.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        _patch_drf_dispatch()  # applied once at startup, idempotent

    def __call__(self, request):
        if request.method not in _ALLOWED_METHODS:
            return JsonResponse(
                {
                    'success': False,
                    'data': None,
                    'message': 'Method not allowed.',
                },
                status=405,
                headers={'Allow': ', '.join(sorted(_ALLOWED_METHODS))},
            )
        return self.get_response(request)
