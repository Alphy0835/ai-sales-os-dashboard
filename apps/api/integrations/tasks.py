from celery import shared_task
from django.utils import timezone

from integrations.models import ConversationRecording, IntegrationSource, MetricSnapshot, Transcription


@shared_task(name="integrations.sync_source")
def sync_integration_source(source_id: str):
    source = IntegrationSource.objects.get(id=source_id)
    if not source.is_enabled:
        return {"source_id": source_id, "skipped": True}

    from integrations.services.sync import run_source_sync

    run_source_sync(source)
    return {"source_id": source_id, "synced": True}


@shared_task(name="integrations.transcribe_recording")
def transcribe_recording_task(recording_id: str):
    recording = ConversationRecording.objects.select_related("employee", "transcription").get(id=recording_id)
    transcription, _ = Transcription.objects.get_or_create(recording=recording)
    transcription.status = Transcription.Status.PROCESSING
    transcription.save(update_fields=["status"])

    recording.status = ConversationRecording.Status.PROCESSING
    recording.save(update_fields=["status"])

    try:
        transcription.text = (
            f"[demo transcript] Разговор с {recording.client_name}. "
            f"Сотрудник {recording.employee.full_name} представился, уточнил потребность клиента "
            f"и договорился о следующем шаге."
        )
        transcription.status = Transcription.Status.COMPLETED
        transcription.completed_at = timezone.now()
        transcription.error_message = ""
        transcription.save()

        recording.status = ConversationRecording.Status.READY
        recording.save(update_fields=["status"])
    except Exception as exc:
        transcription.status = Transcription.Status.FAILED
        transcription.error_message = str(exc)
        transcription.save(update_fields=["status", "error_message"])
        recording.status = ConversationRecording.Status.FAILED
        recording.save(update_fields=["status"])
        raise

    return {"recording_id": recording_id, "status": transcription.status}
