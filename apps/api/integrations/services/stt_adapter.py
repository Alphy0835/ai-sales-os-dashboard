import logging
from pathlib import Path

from django.conf import settings

from ai.services.credentials import AiConfig

logger = logging.getLogger(__name__)


class SttAdapterError(Exception):
    pass


def _client(config: AiConfig):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SttAdapterError("openai package is not installed") from exc

    return OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=120.0,
    )


def transcribe_audio(
    *,
    file_path: str | Path,
    config: AiConfig,
    language: str = "ru",
) -> tuple[str, dict]:
    """Transcribe audio via OpenRouter-compatible STT API."""
    path = Path(file_path)
    if not path.exists():
        raise SttAdapterError(f"Audio file not found: {path}")

    model = getattr(settings, "STT_MODEL", "openai/whisper-1")
    client = _client(config)

    try:
        with path.open("rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                language=language,
            )
    except Exception as exc:
        logger.warning("STT transcription failed: %s", exc)
        raise SttAdapterError(str(exc)) from exc

    text = (response.text or "").strip()
    if not text:
        raise SttAdapterError("Empty STT response")

    content_json = {
        "engine": model,
        "language": language,
        "segments": [{"speaker": "mixed", "text": text}],
    }
    return text, content_json
