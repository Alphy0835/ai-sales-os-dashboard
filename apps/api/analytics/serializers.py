from rest_framework import serializers

from analytics.models import ClientToReview


class ClientToReviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    workspace_name = serializers.CharField(source="workspace.name", read_only=True)

    class Meta:
        model = ClientToReview
        fields = (
            "id",
            "client_name",
            "client_external_id",
            "reason",
            "priority",
            "status",
            "employee_id",
            "employee_name",
            "workspace_id",
            "workspace_name",
            "created_at",
        )
