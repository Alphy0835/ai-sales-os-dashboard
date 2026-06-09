from rest_framework import serializers

from integrations.models import ConversationRecording, IntegrationSource, Transcription


class IntegrationSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationSource
        fields = (
            "id",
            "source_type",
            "name",
            "status",
            "is_enabled",
            "last_sync_at",
            "last_error",
            "workspace_id",
        )


class MetricSummarySerializer(serializers.Serializer):
    period = serializers.CharField()
    as_of = serializers.DateTimeField()
    workspace_id = serializers.UUIDField(allow_null=True)
    user_id = serializers.UUIDField(allow_null=True)
    completeness = serializers.CharField()
    completeness_reason = serializers.CharField(allow_null=True)
    sources = serializers.ListField()
    metrics = serializers.DictField()


class TranscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcription
        fields = ("id", "text", "status", "error_message", "completed_at", "created_at")


class ConversationRecordingSerializer(serializers.ModelSerializer):
    transcription = TranscriptionSerializer(read_only=True)
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_email = serializers.CharField(source="employee.email", read_only=True)

    class Meta:
        model = ConversationRecording
        fields = (
            "id",
            "source_kind",
            "client_name",
            "client_external_id",
            "duration_seconds",
            "status",
            "employee_id",
            "employee_name",
            "employee_email",
            "workspace_id",
            "integration_source_id",
            "created_at",
            "transcription",
        )
        read_only_fields = ("status", "created_at", "transcription")


AUDIO_MAX_SIZE_MB = 100
AUDIO_ALLOWED_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".webm"}


class RecordingCreateSerializer(serializers.Serializer):
    client_name = serializers.CharField(max_length=255)
    client_external_id = serializers.CharField(max_length=128, required=False, default="")
    duration_seconds = serializers.IntegerField(required=False, default=0, min_value=0)
    employee_id = serializers.UUIDField()
    audio_file = serializers.FileField(required=False)

    def validate_audio_file(self, value):
        if value is None:
            return value
        if value.size > AUDIO_MAX_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(f"File too large (max {AUDIO_MAX_SIZE_MB} MB)")
        import os

        ext = os.path.splitext(value.name)[1].lower()
        if ext not in AUDIO_ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(AUDIO_ALLOWED_EXTENSIONS))
            raise serializers.ValidationError(f"Unsupported file type {ext or '(none)'}. Allowed: {allowed}")
        return value

    def validate_employee_id(self, value):
        actor = self.context["request"].user
        from accounts.models import User
        from accounts.services.scope import user_in_scope

        try:
            employee = User.objects.get(id=value, tenant_id=actor.tenant_id, role=User.Role.EMPLOYEE)
        except User.DoesNotExist:
            raise serializers.ValidationError("Employee not found")
        if actor.role == User.Role.EMPLOYEE and employee.id != actor.id:
            raise serializers.ValidationError("Employees can only upload own recordings")
        if actor.role == User.Role.MANAGER and not user_in_scope(actor, employee):
            raise serializers.ValidationError("Employee outside your scope")
        return value
