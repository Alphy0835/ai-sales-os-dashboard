from django.urls import path

from accounts.views import (
    LoginView,
    LogoutView,
    MeView,
    PermissionAuditView,
    PermissionUserDetailView,
    PermissionUserListView,
    RefreshView,
    ScopeUserAccessView,
    ScopeView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("scope/", ScopeView.as_view(), name="scope"),
    path("scope/users/<uuid:user_id>/", ScopeUserAccessView.as_view(), name="scope-user-access"),
    path("permissions/users/", PermissionUserListView.as_view(), name="permission-user-list"),
    path(
        "permissions/users/<uuid:user_id>/",
        PermissionUserDetailView.as_view(),
        name="permission-user-detail",
    ),
    path("audit/permissions/", PermissionAuditView.as_view(), name="permission-audit"),
]
