from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from accounts.models import ManagerScope, ModulePermission, Tenant, User, Workspace
from integrations.models import ConversationRecording, IntegrationSource, MetricSnapshot, Transcription
from integrations.services.stt_adapter import SttAdapterError


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, OPENROUTER_API_KEY="test-key")
class SttTranscriptionTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="STT Co", slug="stt-co")
        self.workspace = Workspace.objects.create(tenant=self.tenant, name="Office")
        self.employee = User.objects.create_user(
            email="emp@stt.local",
            password="pass1234",
            tenant=self.tenant,
            workspace=self.workspace,
            full_name="Employee",
            role=User.Role.EMPLOYEE,
        )
        ModulePermission.objects.update_or_create(
            user=self.employee,
            module=ModulePermission.Module.DASHBOARD,
            defaults={"level": ModulePermission.Level.VIEW},
        )

    @patch("integrations.services.stt_adapter.transcribe_audio")
    def test_stt_used_when_audio_present(self, mock_stt):
        mock_stt.return_value = (
            "Real transcript text",
            {"engine": "openai/whisper-1", "language": "ru", "segments": []},
        )
        recording = ConversationRecording.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            source_kind=ConversationRecording.SourceKind.MANUAL,
            client_name="Client",
            status=ConversationRecording.Status.UPLOADED,
        )
        recording.audio_file.save("test.webm", ContentFile(b"fake-audio"), save=True)
        Transcription.objects.create(recording=recording, status=Transcription.Status.PENDING)

        from integrations.tasks import transcribe_recording_task

        transcribe_recording_task(str(recording.id))
        transcription = Transcription.objects.get(recording=recording)
        self.assertEqual(transcription.status, Transcription.Status.COMPLETED)
        self.assertEqual(transcription.content_json["engine"], "openai/whisper-1")
        recording.refresh_from_db()
        self.assertFalse(recording.audio_file)

    @override_settings(OPENROUTER_API_KEY="")
    def test_demo_fallback_without_api_key(self):
        recording = ConversationRecording.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            source_kind=ConversationRecording.SourceKind.MANUAL,
            client_name="Client",
            status=ConversationRecording.Status.UPLOADED,
        )
        Transcription.objects.create(recording=recording, status=Transcription.Status.PENDING)

        from integrations.tasks import transcribe_recording_task

        transcribe_recording_task(str(recording.id))
        transcription = Transcription.objects.get(recording=recording)
        self.assertEqual(transcription.content_json["engine"], "demo_v1")

    @override_settings(OPENROUTER_API_KEY="test-key")
    @patch("integrations.services.stt_adapter.transcribe_audio", side_effect=SttAdapterError("fail"))
    def test_demo_fallback_on_stt_error(self, mock_stt):
        recording = ConversationRecording.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            employee=self.employee,
            source_kind=ConversationRecording.SourceKind.MANUAL,
            client_name="Client",
            status=ConversationRecording.Status.UPLOADED,
        )
        recording.audio_file.save("test.webm", ContentFile(b"fake-audio"), save=True)
        Transcription.objects.create(recording=recording, status=Transcription.Status.PENDING)

        from integrations.tasks import transcribe_recording_task

        transcribe_recording_task(str(recording.id))
        transcription = Transcription.objects.get(recording=recording)
        self.assertEqual(transcription.content_json["engine"], "demo_v1")
