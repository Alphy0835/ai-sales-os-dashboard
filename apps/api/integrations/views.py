from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ModulePermission, User
from accounts.services.permissions import get_user_permissions
from accounts.services.scope import get_scoped_workspace_ids
from integrations.models import ConversationRecording, IntegrationSource, Transcription
from integrations.serializers import (
    ConversationRecordingSerializer,
    IntegrationSourceSerializer,
    MetricSummarySerializer,
    RecordingCreateSerializer,
    TranscriptionSerializer,
)
from integrations.services.aggregation import build_metrics_summary
from integrations.services.scope import can_access_recording, recordings_queryset
from integrations.tasks import transcribe_recording_task


def require_dashboard_view(user):
    perms = get_user_permissions(user)
    if perms.get(ModulePermission.Module.DASHBOARD) == ModulePermission.Level.NONE:
        raise PermissionDenied("Dashboard view permission required")


class IntegrationSourceListView(APIView):
    def get(self, request):
        require_dashboard_view(request.user)
        workspace_ids = get_scoped_workspace_ids(request.user)
        qs = IntegrationSource.objects.filter(
            tenant_id=request.user.tenant_id,
            is_enabled=True,
        )
        if request.user.role == User.Role.MANAGER and workspace_ids:
            from django.db.models import Q

            qs = qs.filter(Q(workspace_id__in=workspace_ids) | Q(workspace__isnull=True))
        return Response(IntegrationSourceSerializer(qs, many=True).data)


class MetricsSummaryView(APIView):
    def get(self, request):
        require_dashboard_view(request.user)
        period = request.query_params.get("period", "today")
        if period not in ("today", "week", "month"):
            return Response({"period": "Must be today, week, or month"}, status=400)

        summary = build_metrics_summary(
            actor=request.user,
            period=period,
            workspace_id=request.query_params.get("workspace_id"),
            user_id=request.query_params.get("user_id"),
        )
        if summary is None:
            raise NotFound("Metrics not available for requested scope")
        return Response(MetricSummarySerializer(summary).data)


class RecordingListCreateView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        require_dashboard_view(request.user)
        qs = recordings_queryset(request.user)
        return Response(ConversationRecordingSerializer(qs[:100], many=True).data)

    def post(self, request):
        require_dashboard_view(request.user)
        serializer = RecordingCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        employee = User.objects.get(id=serializer.validated_data["employee_id"])
        audio_file = serializer.validated_data.get("audio_file")
        if audio_file is not None:
            audio_file.seek(0)
        recording = ConversationRecording.objects.create(
            tenant_id=request.user.tenant_id,
            workspace_id=employee.workspace_id,
            employee=employee,
            source_kind=ConversationRecording.SourceKind.MANUAL,
            client_name=serializer.validated_data["client_name"],
            client_external_id=serializer.validated_data.get("client_external_id", ""),
            duration_seconds=serializer.validated_data.get("duration_seconds") or 0,
            status=ConversationRecording.Status.UPLOADED,
        )
        Transcription.objects.create(
            recording=recording,
            status=Transcription.Status.PENDING,
        )
        transcribe_recording_task.delay(str(recording.id))
        return Response(ConversationRecordingSerializer(recording).data, status=status.HTTP_201_CREATED)


class RecordingDetailView(APIView):
    def get(self, request, recording_id):
        require_dashboard_view(request.user)
        try:
            recording = recordings_queryset(request.user).get(id=recording_id)
        except ConversationRecording.DoesNotExist:
            raise NotFound("Recording not found")
        return Response(ConversationRecordingSerializer(recording).data)


class RecordingTranscriptionView(APIView):
    def get(self, request, recording_id):
        require_dashboard_view(request.user)
        try:
            recording = ConversationRecording.objects.select_related("transcription").get(
                id=recording_id,
                tenant_id=request.user.tenant_id,
            )
        except ConversationRecording.DoesNotExist:
            raise NotFound("Recording not found")
        if not can_access_recording(request.user, recording):
            raise PermissionDenied("Recording outside your scope")
        if not hasattr(recording, "transcription"):
            raise NotFound("Transcription not found")
        return Response(TranscriptionSerializer(recording.transcription).data)

    def post(self, request, recording_id):
        require_dashboard_view(request.user)
        try:
            recording = ConversationRecording.objects.get(
                id=recording_id,
                tenant_id=request.user.tenant_id,
            )
        except ConversationRecording.DoesNotExist:
            raise NotFound("Recording not found")
        if not can_access_recording(request.user, recording):
            raise PermissionDenied("Recording outside your scope")

        transcription, _ = Transcription.objects.get_or_create(
            recording=recording,
            defaults={"status": Transcription.Status.PENDING},
        )
        transcription.status = Transcription.Status.PENDING
        transcription.save(update_fields=["status"])
        transcribe_recording_task.delay(str(recording.id))
        return Response({"status": "queued", "recording_id": str(recording.id)})
