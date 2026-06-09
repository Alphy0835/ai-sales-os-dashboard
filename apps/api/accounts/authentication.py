from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError

from accounts.cookies import ACCESS_COOKIE


class CookieJWTAuthentication(JWTAuthentication):
    """Read JWT from httpOnly cookie; fall back to Authorization Bearer (tests, API clients)."""

    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                validated_token = self.get_validated_token(raw_token)
                return self.get_user(validated_token), validated_token

        raw_token = request.COOKIES.get(ACCESS_COOKIE)
        if not raw_token:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError:
            return None

        return self.get_user(validated_token), validated_token
