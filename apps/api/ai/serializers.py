from rest_framework import serializers

from ai.models import AgentChatMessage, AgentChatSession, AnalyticsReport, CustomReport, KnowledgeArticle, QualityCriterion


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
        required=False,
        default=AnalyticsReport.Template.STANDARD_QUALITY,
    )
    custom_report_id = serializers.UUIDField(required=False, allow_null=True)


class AnalyticsReportSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source="workspace.name", read_only=True)
    employee_name = serializers.SerializerMethodField()
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    template_label = serializers.SerializerMethodField()
    custom_report_title = serializers.SerializerMethodField()

    class Meta:
        model = AnalyticsReport
        fields = [
            "id",
            "template",
            "template_label",
            "custom_report_title",
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
        if obj.custom_report_id:
            return obj.custom_report.title
        return dict(AnalyticsReport.Template.choices).get(obj.template, obj.template)

    def get_custom_report_title(self, obj):
        return obj.custom_report.title if obj.custom_report_id else None


class CustomReportSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = CustomReport
        fields = [
            "id",
            "title",
            "description",
            "structured_query",
            "is_active",
            "author_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["structured_query", "created_at", "updated_at", "author_name"]


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    category_label = serializers.SerializerMethodField()
    access_label = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeArticle
        fields = [
            "id",
            "title",
            "category",
            "category_label",
            "content",
            "tags",
            "access_level",
            "access_label",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_category_label(self, obj):
        return dict(KnowledgeArticle.Category.choices).get(obj.category, obj.category)

    def get_access_label(self, obj):
        return dict(KnowledgeArticle.AccessLevel.choices).get(obj.access_level, obj.access_level)


class AgentChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    session_id = serializers.UUIDField(required=False, allow_null=True)
    client_name = serializers.CharField(required=False, allow_blank=True, default="")
    client_note = serializers.CharField(required=False, allow_blank=True, default="")


class AgentChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentChatMessage
        fields = ["id", "role", "content", "sources", "created_at"]


class AgentChatSessionSerializer(serializers.ModelSerializer):
    messages = AgentChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AgentChatSession
        fields = ["id", "client_name", "client_note", "messages", "created_at", "updated_at"]
