from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from accounts.models import AuditLog, RegistrationInvite, User
from accounts.serializers_auth import CookieTokenRefreshSerializer
from accounts.serializers import (
    AuditLogSerializer,
    KnowledgeGrantUpdateSerializer,
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
from ai.services.knowledge_grants import KnowledgeGrantError, list_knowledge_grants, update_knowledge_grants


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

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get("email")
            if email:
                user = User.objects.filter(email__iexact=email, is_active=True).first()
                if user:
                    from integrations.models import IntegrationSource
                    from integrations.tasks import should_sync_source, trigger_tenant_crm_sync

                    crm_sources = IntegrationSource.objects.filter(
                        tenant_id=user.tenant_id,
                        is_enabled=True,
                        source_type=IntegrationSource.SourceType.CRM,
                        config_json__provider="google_sheets",
                    ).exclude(credentials_encrypted="")
                    if any(should_sync_source(source) for source in crm_sources):
                        trigger_tenant_crm_sync.delay(str(user.tenant_id))
        return response

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.status_code == 200 and isinstance(response.data, dict):
            set_auth_cookies(response, response.data.get("access"), response.data.get("refresh"))
        return response


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField(max_length=255)
    invite_code = serializers.CharField(max_length=64)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    @transaction.atomic
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            invite = RegistrationInvite.objects.select_for_update().get(code=data["invite_code"])
        except RegistrationInvite.DoesNotExist:
            raise ValidationError({"invite_code": "Invalid invite code"})

        if invite.expires_at <= timezone.now():
            raise ValidationError({"invite_code": "Invite has expired"})
        if invite.use_count >= invite.max_uses:
            raise ValidationError({"invite_code": "Invite has reached maximum uses"})

        email = data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError({"email": "A user with this email already exists"})

        user = User.objects.create_user(
            email=email,
            password=data["password"],
            tenant=invite.tenant,
            workspace=invite.workspace,
            full_name=data["full_name"],
            role=invite.role,
        )

        invite.use_count += 1
        update_fields = ["use_count"]
        if invite.used_at is None:
            invite.used_at = timezone.now()
            update_fields.append("used_at")
        invite.save(update_fields=update_fields)

        refresh = RefreshToken.for_user(user)
        refresh["tenant_id"] = str(user.tenant_id)
        refresh["role"] = user.role
        access = refresh.access_token
        access["tenant_id"] = str(user.tenant_id)
        access["role"] = user.role

        response = Response(
            {
                "refresh": str(refresh),
                "access": str(access),
                "user": UserBriefSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )
        set_auth_cookies(response, str(access), str(refresh))
        return response


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    serializer_class = CookieTokenRefreshSerializer
    throttle_classes = [LoginRateThrottle]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.status_code == 200 and isinstance(response.data, dict):
            set_auth_cookies(
                response,
                response.data.get("access"),
                response.data.get("refresh"),
            )
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE)
        if not refresh_token and isinstance(request.data, dict):
            refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookies(response)
        return response


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

        qs = AuditLog.objects.filter(tenant_id=request.user.tenant_id).select_related(
            "actor", "target_user", "actor__tenant", "actor__workspace", "target_user__workspace"
        )

        action_param = request.query_params.get("action")
        if action_param:
            valid = {choice[0] for choice in AuditLog.Action.choices}
            actions = [part.strip() for part in action_param.split(",") if part.strip()]
            invalid = [action for action in actions if action not in valid]
            if invalid:
                raise ValidationError({"action": f"Unknown action(s): {', '.join(invalid)}"})
            qs = qs.filter(action__in=actions)
        else:
            qs = qs.filter(action=AuditLog.Action.PERMISSION_CHANGE)

        target_user_id = request.query_params.get("user_id")
        if target_user_id:
            qs = qs.filter(target_user_id=target_user_id)

        try:
            limit = min(int(request.query_params.get("limit", 50)), 200)
        except (TypeError, ValueError):
            limit = 50
        logs = qs[:limit]
        return Response({"results": AuditLogSerializer(logs, many=True).data})


class PermissionKnowledgeView(APIView):
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
        return Response({"grants": list_knowledge_grants(grantor=request.user, target=target)})

    def put(self, request, user_id):
        if not can_grant_permissions(request.user):
            raise PermissionDenied("Settings edit permission required")

        target = self._get_target(request, user_id)
        serializer = KnowledgeGrantUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            grants = update_knowledge_grants(
                grantor=request.user,
                target=target,
                grants=serializer.validated_data["grants"],
                ip_address=client_ip(request),
            )
        except KnowledgeGrantError as exc:
            if exc.code == "scope_denied":
                raise PermissionDenied(str(exc))
            if exc.code == "ceiling_violation":
                raise ValidationError({"grants": str(exc)})
            raise ValidationError(str(exc))

        return Response({"grants": grants})
