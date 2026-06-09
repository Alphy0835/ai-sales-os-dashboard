from django.core.management.base import BaseCommand

from accounts.models import Tenant, User, Workspace
from integrations.models import ConversationRecording, IntegrationSource, Transcription
from integrations.services.sync import run_source_sync
from integrations.tasks import transcribe_recording_task


def seed_integration_sources(tenant, moscow, spb):
    sources = []

    def upsert(workspace, source_type, name, status):
        source, _ = IntegrationSource.objects.update_or_create(
            tenant=tenant,
            workspace=workspace,
            source_type=source_type,
            name=name,
            defaults={
                "status": status,
                "is_enabled": True,
                "last_error": "" if status != IntegrationSource.Status.ERROR else "Connection timeout",
            },
        )
        sources.append(source)
        return source

    upsert(moscow, IntegrationSource.SourceType.CRM, "Demo CRM", IntegrationSource.Status.CONNECTED)
    upsert(
        moscow,
        IntegrationSource.SourceType.TELEPHONY,
        "Demo Telephony",
        IntegrationSource.Status.DEGRADED,
    )
    upsert(moscow, IntegrationSource.SourceType.REPORTING, "Demo Reporting", IntegrationSource.Status.CONNECTED)
    upsert(spb, IntegrationSource.SourceType.CRM, "Demo CRM SPB", IntegrationSource.Status.CONNECTED)
    upsert(
        spb,
        IntegrationSource.SourceType.TELEPHONY,
        "Demo Telephony SPB",
        IntegrationSource.Status.DISCONNECTED,
    )
    return sources


class Command(BaseCommand):
    help = "Seed demo integration sources, metrics sync, and sample recording"

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(slug="demo").first()
        if not tenant:
            self.stdout.write(self.style.ERROR("Run seed_demo first"))
            return

        moscow = Workspace.objects.filter(tenant=tenant, name="ОП Москва").first()
        spb = Workspace.objects.filter(tenant=tenant, name="ОП СПб").first()
        if not moscow or not spb:
            self.stdout.write(self.style.ERROR("Demo workspaces missing"))
            return

        sources = seed_integration_sources(tenant, moscow, spb)
        for source in sources:
            if source.status not in (
                IntegrationSource.Status.DISCONNECTED,
                IntegrationSource.Status.ERROR,
            ):
                run_source_sync(source)

        employee = User.objects.filter(tenant=tenant, email="employee@demo.local").first()
        telephony = next(
            s for s in sources if s.workspace_id == moscow.id and s.source_type == IntegrationSource.SourceType.TELEPHONY
        )
        if employee:
            recording, created = ConversationRecording.objects.get_or_create(
                tenant=tenant,
                employee=employee,
                client_name="Иван Петров",
                source_kind=ConversationRecording.SourceKind.TELEPHONY,
                defaults={
                    "workspace": moscow,
                    "integration_source": telephony,
                    "duration_seconds": 420,
                    "status": ConversationRecording.Status.UPLOADED,
                    "client_external_id": "crm-client-001",
                },
            )
            if created or not hasattr(recording, "transcription"):
                Transcription.objects.get_or_create(
                    recording=recording,
                    defaults={"status": Transcription.Status.PENDING},
                )
                transcribe_recording_task.delay(str(recording.id))
            elif hasattr(recording, "transcription") and recording.transcription.status != Transcription.Status.COMPLETED:
                transcribe_recording_task.delay(str(recording.id))

        self.stdout.write(self.style.SUCCESS("Integration demo data ready"))
