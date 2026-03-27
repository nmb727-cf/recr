"""
Custom authentication classes for TalentOS.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed


class SilentJWTAuthentication(JWTAuthentication):
    """
    JWT authenticator that treats malformed Authorization headers as
    unauthenticated (anonymous) rather than raising AuthenticationFailed.

    Standard JWTAuthentication raises AuthenticationFailed when the
    Authorization header starts with the expected prefix (e.g. "Bearer")
    but has the wrong number of space-delimited parts.  This causes
    AllowAny endpoints to return 401 when a client sends a syntactically
    broken auth header — incorrect behaviour since the endpoint doesn't
    require auth at all.

    Behaviour matrix (unchanged for valid flows):
      - No Authorization header          → None (anonymous)   same as before
      - Authorization: <non-Bearer>      → None (anonymous)   same as before
      - Authorization: Bearer <valid>    → (user, token)      same as before
      - Authorization: Bearer <invalid>  → None (anonymous)   was: 401 ← fixed
      - Authorization: Bearer (no token) → None (anonymous)   was: 401 ← fixed

    For IsAuthenticated views the anonymous user still triggers a 401 via
    permission checking, so authenticated endpoints are unaffected.
    """

    def get_raw_token(self, header: bytes):
        try:
            return super().get_raw_token(header)
        except AuthenticationFailed:
            # Malformed header — treat as no credentials provided.
            return None
