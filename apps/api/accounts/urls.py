from django.urls import path

from accounts.views import (
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PermissionAuditView,
    PermissionKnowledgeView,
    PermissionUserDetailView,
    PermissionUserListView,
    RefreshView,
    RegisterView,
    ScopeUserAccessView,
    ScopeView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("scope/", ScopeView.as_view(), name="scope"),
    path("scope/users/<uuid:user_id>/", ScopeUserAccessView.as_view(), name="scope-user-access"),
    path("permissions/users/", PermissionUserListView.as_view(), name="permission-user-list"),
    path(
        "permissions/users/<uuid:user_id>/",
        PermissionUserDetailView.as_view(),
        name="permission-user-detail",
    ),
    path("audit/permissions/", PermissionAuditView.as_view(), name="permission-audit"),
    path(
        "permissions/users/<uuid:user_id>/knowledge/",
        PermissionKnowledgeView.as_view(),
        name="permission-knowledge",
    ),
]
