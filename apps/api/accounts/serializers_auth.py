from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from accounts.cookies import REFRESH_COOKIE


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = serializers.CharField(required=False)

    def validate(self, attrs):
        if not attrs.get("refresh"):
            request = self.context.get("request")
            if request is not None:
                cookie_refresh = request.COOKIES.get(REFRESH_COOKIE)
                if cookie_refresh:
                    attrs["refresh"] = cookie_refresh
        if not attrs.get("refresh"):
            raise serializers.ValidationError({"refresh": "Refresh token required."})
        return super().validate(attrs)
