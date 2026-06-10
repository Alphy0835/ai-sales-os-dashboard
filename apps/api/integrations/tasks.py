import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from integrations.models import ConversationRecording, IntegrationSource, Transcription
from integrations.services.health import crm_stale_reason, crm_sync_interval_minutes, is_crm_source_stale

logger = logging.getLogger(__name__)


def should_sync_source(source: IntegrationSource, *, force: bool = False) -> bool:
    if force:
        return True
    if not source.is_enabled:
        return False
    interval_minutes = getattr(settings, "CRM_SYNC_INTERVAL_MINUTES", 60)
    if source.last_sync_at is None:
        return True
    elapsed = timezone.now() - source.last_sync_at
    return elapsed >= timezone.timedelta(minutes=interval_minutes)


@shared_task(name="integrations.sync_source")
def sync_integration_source(source_id: str, force: bool = False):
    source = IntegrationSource.objects.get(id=source_id)
    if not source.is_enabled:
        return {"source_id": source_id, "skipped": True}
    if not should_sync_source(source, force=force):
        return {"source_id": source_id, "skipped": True, "reason": "throttled"}

    from integrations.services.sync import run_source_sync

    run_source_sync(source)
    return {"source_id": source_id, "synced": True}


@shared_task(name="integrations.sync_all_sources")
def sync_all_sources() -> dict:
    source_ids = list(
        IntegrationSource.objects.filter(is_enabled=True).values_list("id", flat=True)
    )
    queued = 0
    for source_id in source_ids:
        source = IntegrationSource.objects.get(id=source_id)
        if should_sync_source(source):
            if source.source_type == IntegrationSource.SourceType.CRM and is_crm_source_stale(source):
                logger.warning(
                    "CRM source %s stale; queued catch-up sync (last_sync_at=%s)",
                    source_id,
                    source.last_sync_at,
                )
            sync_integration_source.delay(str(source_id))
            queued += 1
        elif source.source_type == IntegrationSource.SourceType.CRM:
            if is_crm_source_stale(source):
                logger.warning(
                    "CRM source %s skipped but data is stale: %s",
                    source_id,
                    crm_stale_reason(source),
                )
            else:
                logger.info(
                    "CRM source %s skipped (throttled, last_sync_at=%s, interval=%s min)",
                    source_id,
                    source.last_sync_at,
                    crm_sync_interval_minutes(),
                )
    return {"queued": queued, "total": len(source_ids)}


@shared_task(name="integrations.trigger_tenant_crm_sync")
def trigger_tenant_crm_sync(tenant_id: str, force: bool = False) -> dict:
    sources = IntegrationSource.objects.filter(
        tenant_id=tenant_id,
        is_enabled=True,
        source_type=IntegrationSource.SourceType.CRM,
        config_json__provider="google_sheets",
    ).exclude(credentials_encrypted="")
    queued = 0
    for source in sources:
        if should_sync_source(source, force=force):
            sync_integration_source.delay(str(source.id), force=force)
            queued += 1
    return {"tenant_id": tenant_id, "queued": queued}


def _demo_transcript(recording: ConversationRecording) -> tuple[str, dict]:
    text = (
        f"[demo transcript] Разговор с {recording.client_name}. "
        f"Сотрудник {recording.employee.full_name} представился, уточнил потребность клиента "
        f"и договорился о следующем шаге."
    )
    content_json = {
        "engine": "demo_v1",
        "language": "ru",
        "segments": [{"speaker": "mixed", "text": text}],
    }
    return text, content_json


def _transcribe_recording(recording: ConversationRecording) -> tuple[str, dict]:
    from ai.services.credentials import llm_available, resolve_ai_config
    from integrations.services.stt_adapter import SttAdapterError, transcribe_audio

    if recording.audio_file:
        config = resolve_ai_config(recording.employee)
        if llm_available(config):
            try:
                return transcribe_audio(
                    file_path=recording.audio_file.path,
                    config=config,
                    language="ru",
                )
            except SttAdapterError:
                pass

    return _demo_transcript(recording)


@shared_task(name="integrations.transcribe_recording")
def transcribe_recording_task(recording_id: str):
    recording = ConversationRecording.objects.select_related("employee", "transcription").get(id=recording_id)
    transcription, _ = Transcription.objects.get_or_create(recording=recording)
    transcription.status = Transcription.Status.PROCESSING
    transcription.save(update_fields=["status"])

    recording.status = ConversationRecording.Status.PROCESSING
    recording.save(update_fields=["status"])

    try:
        text, content_json = _transcribe_recording(recording)
        transcription.text = text
        transcription.content_json = content_json
        transcription.status = Transcription.Status.COMPLETED
        transcription.completed_at = timezone.now()
        transcription.error_message = ""
        transcription.save()

        if recording.audio_file:
            recording.audio_file.delete(save=True)

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


@shared_task(name="integrations.purge_expired_transcripts")
def purge_expired_transcripts() -> dict:
    retention_days = getattr(settings, "TRANSCRIPT_RETENTION_DAYS", 90)
    cutoff = timezone.now() - timezone.timedelta(days=retention_days)
    qs = ConversationRecording.objects.filter(created_at__lt=cutoff)
    count = qs.count()
    qs.delete()
    return {"deleted": count, "retention_days": retention_days}
