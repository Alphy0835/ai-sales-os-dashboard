from rest_framework import serializers

from accounts.models import AuditLog, ModulePermission, User, Workspace
from accounts.services.permissions import get_user_permissions


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ("id", "name")


class UserBriefSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    workspace_id = serializers.UUIDField(source="workspace.id", read_only=True, allow_null=True)
    workspace_name = serializers.CharField(source="workspace.name", read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "role",
            "tenant_id",
            "workspace_id",
            "workspace_name",
        )


class ScopeUserSerializer(serializers.ModelSerializer):
    workspace = WorkspaceSerializer(read_only=True)
    manager_id = serializers.UUIDField(source="manager.id", read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "workspace", "manager_id")


class MeSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    workspace = WorkspaceSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()
    scope = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "role",
            "tenant_id",
            "workspace",
            "permissions",
            "scope",
        )

    def get_permissions(self, user):
        return get_user_permissions(user)

    def get_scope(self, user):
        from accounts.services.scope import get_scoped_workspaces

        workspaces = get_scoped_workspaces(user)
        return {"workspaces": WorkspaceSerializer(workspaces, many=True).data}


class UserPermissionsSerializer(serializers.ModelSerializer):
    workspace = WorkspaceSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "workspace", "permissions")

    def get_permissions(self, user):
        return get_user_permissions(user)


class PermissionUpdateSerializer(serializers.Serializer):
    permissions = serializers.DictField(child=serializers.CharField())

    def validate_permissions(self, value):
        if not value:
            raise serializers.ValidationError("At least one module permission is required.")
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    actor = UserBriefSerializer(read_only=True)
    target_user = UserBriefSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "action",
            "module",
            "old_level",
            "new_level",
            "actor",
            "target_user",
            "created_at",
        )
