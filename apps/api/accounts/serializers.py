from rest_framework import serializers

from accounts.models import ModulePermission, User, Workspace


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


class MeSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    workspace = WorkspaceSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()

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
        )

    def get_permissions(self, user):
        perms = {m.module: m.level for m in user.module_permissions.all()}
        for module in ModulePermission.Module.values:
            perms.setdefault(module, ModulePermission.Level.NONE)
        return perms
