from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.models import AuditLog, User
from accounts.serializers import (
    AuditLogSerializer,
    MeSerializer,
    PermissionUpdateSerializer,
    ScopeUserSerializer,
    UserBriefSerializer,
    UserPermissionsSerializer,
    WorkspaceSerializer,
)
from accounts.services.audit import log_scope_denied
from accounts.services.grant import PermissionGrantError, grant_permissions
from accounts.services.permissions import can_grant_permissions, can_view_audit, get_user_permissions
from accounts.services.scope import get_accessible_users, get_scoped_workspaces, user_in_scope


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["tenant_id"] = str(user.tenant_id)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserBriefSerializer(self.user).data
        return data


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)


class LogoutView(APIView):
    def post(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScopeView(APIView):
    """Workspaces and users visible to the authenticated manager."""

    def get(self, request):
        user = request.user
        workspaces = get_scoped_workspaces(user)
        accessible = get_accessible_users(user)
        return Response(
            {
                "workspaces": WorkspaceSerializer(workspaces, many=True).data,
                "users": ScopeUserSerializer(accessible, many=True).data,
            }
        )


class ScopeUserAccessView(APIView):
    """Check whether a target user is within actor scope."""

    def get(self, request, user_id):
        try:
            target = User.objects.get(id=user_id, tenant_id=request.user.tenant_id, is_active=True)
        except User.DoesNotExist:
            raise NotFound("User not found")

        if not user_in_scope(request.user, target):
            log_scope_denied(actor=request.user, target_user=target, ip_address=client_ip(request))
            raise PermissionDenied("User is outside your scope")

        return Response(
            {
                "accessible": True,
                "user": ScopeUserSerializer(target).data,
                "permissions": get_user_permissions(target),
            }
        )


class PermissionUserListView(APIView):
    def get(self, request):
        if not can_grant_permissions(request.user) and not can_view_audit(request.user):
            raise PermissionDenied("Settings view or edit permission required")

        accessible = get_accessible_users(request.user)
        return Response(UserPermissionsSerializer(accessible, many=True).data)


class PermissionUserDetailView(APIView):
    def _get_target(self, request, user_id):
        try:
            target = User.objects.select_related("workspace").get(
                id=user_id,
                tenant_id=request.user.tenant_id,
                is_active=True,
            )
        except User.DoesNotExist:
            raise NotFound("User not found")

        if not user_in_scope(request.user, target):
            log_scope_denied(actor=request.user, target_user=target, ip_address=client_ip(request))
            raise PermissionDenied("User is outside your scope")
        return target

    def get(self, request, user_id):
        if not can_grant_permissions(request.user) and not can_view_audit(request.user):
            raise PermissionDenied("Settings view or edit permission required")
        target = self._get_target(request, user_id)
        return Response(UserPermissionsSerializer(target).data)

    def put(self, request, user_id):
        if not can_grant_permissions(request.user):
            raise PermissionDenied("Settings edit permission required")

        target = self._get_target(request, user_id)
        serializer = PermissionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            permissions = grant_permissions(
                grantor=request.user,
                target_user=target,
                permissions=serializer.validated_data["permissions"],
                ip_address=client_ip(request),
            )
        except PermissionGrantError as exc:
            if exc.code == "scope_denied":
                raise PermissionDenied(str(exc))
            if exc.code == "ceiling_violation":
                raise ValidationError({"permissions": exc.args[0]})
            raise ValidationError(str(exc))

        return Response(
            {
                **UserPermissionsSerializer(target).data,
                "permissions": permissions,
            }
        )


class PermissionAuditView(APIView):
    def get(self, request):
        if not can_view_audit(request.user):
            raise PermissionDenied("Settings view or edit permission required")

        qs = AuditLog.objects.filter(
            tenant_id=request.user.tenant_id,
            action=AuditLog.Action.PERMISSION_CHANGE,
        ).select_related("actor", "target_user", "actor__tenant", "actor__workspace", "target_user__workspace")

        target_user_id = request.query_params.get("user_id")
        if target_user_id:
            qs = qs.filter(target_user_id=target_user_id)

        try:
            limit = min(int(request.query_params.get("limit", 50)), 200)
        except (TypeError, ValueError):
            limit = 50
        logs = qs[:limit]
        return Response({"results": AuditLogSerializer(logs, many=True).data})
