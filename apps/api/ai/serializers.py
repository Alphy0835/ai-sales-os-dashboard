from rest_framework import serializers

from ai.models import AnalyticsReport, QualityCriterion


class QualityCriterionSerializer(serializers.ModelSerializer):
    stage_label = serializers.SerializerMethodField()

    class Meta:
        model = QualityCriterion
        fields = [
            "id",
            "name",
            "description",
            "funnel_stage",
            "stage_label",
            "keywords",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_stage_label(self, obj):
        return dict(QualityCriterion.FunnelStage.choices).get(obj.funnel_stage, obj.funnel_stage)


class ReportRunSerializer(serializers.Serializer):
    workspace_id = serializers.UUIDField()
    employee_id = serializers.UUIDField(required=False, allow_null=True)
    template = serializers.ChoiceField(
        choices=AnalyticsReport.Template.choices,
        default=AnalyticsReport.Template.STANDARD_QUALITY,
    )


class AnalyticsReportSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source="workspace.name", read_only=True)
    employee_name = serializers.SerializerMethodField()
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    template_label = serializers.SerializerMethodField()

    class Meta:
        model = AnalyticsReport
        fields = [
            "id",
            "template",
            "template_label",
            "status",
            "workspace_id",
            "workspace_name",
            "employee_id",
            "employee_name",
            "author_name",
            "summary_text",
            "canvas",
            "error_message",
            "recordings_analyzed",
            "created_at",
        ]

    def get_employee_name(self, obj):
        return obj.employee.full_name if obj.employee_id else None

    def get_template_label(self, obj):
        return dict(AnalyticsReport.Template.choices).get(obj.template, obj.template)
