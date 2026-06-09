from django.conf import settings

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _cookie_params():
    return {
        "httponly": True,
        "secure": settings.USE_HTTPS_SETTINGS,
        "samesite": "Lax",
        "path": "/",
    }


def set_auth_cookies(response, access: str | None, refresh: str | None) -> None:
    params = _cookie_params()
    if access:
        response.set_cookie(
            ACCESS_COOKIE,
            access,
            max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
            **params,
        )
    if refresh:
        response.set_cookie(
            REFRESH_COOKIE,
            refresh,
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            **params,
        )


def clear_auth_cookies(response) -> None:
    params = _cookie_params()
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(
            name,
            path=params["path"],
            samesite=params["samesite"],
        )
