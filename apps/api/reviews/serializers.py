from rest_framework import serializers

from reviews.models import Review, ReviewTask


class ReviewTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewTask
        fields = ["id", "title", "status", "created_at", "updated_at", "completed_at"]


class ReviewListSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_id = serializers.UUIDField(source="employee.id", read_only=True)
    workspace_name = serializers.CharField(source="workspace.name", read_only=True)
    workspace_id = serializers.UUIDField(source="workspace.id", read_only=True)
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    client_name = serializers.SerializerMethodField()
    tasks = ReviewTaskSerializer(many=True, read_only=True)
    tasks_done = serializers.SerializerMethodField()
    tasks_total = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "employee_id",
            "employee_name",
            "workspace_id",
            "workspace_name",
            "author_name",
            "client_name",
            "comment",
            "discussion",
            "created_at",
            "tasks",
            "tasks_done",
            "tasks_total",
        ]

    def get_client_name(self, obj):
        if obj.client_to_review_id:
            return obj.client_to_review.client_name
        return None

    def get_tasks_done(self, obj):
        return sum(1 for t in obj.tasks.all() if t.status == ReviewTask.Status.DONE)

    def get_tasks_total(self, obj):
        return obj.tasks.count()


class ReviewCreateSerializer(serializers.Serializer):
    employee_id = serializers.UUIDField()
    workspace_id = serializers.UUIDField()
    comment = serializers.CharField()
    discussion = serializers.CharField(required=False, allow_blank=True, default="")
    client_id = serializers.UUIDField(required=False, allow_null=True)
    tasks = serializers.ListField(child=serializers.CharField(max_length=500), allow_empty=True)


class EmployeeTaskSerializer(serializers.ModelSerializer):
    review_id = serializers.UUIDField(source="review.id", read_only=True)
    review_date = serializers.DateTimeField(source="review.created_at", read_only=True)
    author_name = serializers.CharField(source="review.author.full_name", read_only=True)
    workspace_name = serializers.CharField(source="review.workspace.name", read_only=True)

    class Meta:
        model = ReviewTask
        fields = [
            "id",
            "title",
            "status",
            "review_id",
            "review_date",
            "author_name",
            "workspace_name",
            "updated_at",
        ]


class TaskStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ReviewTask.Status.choices)
