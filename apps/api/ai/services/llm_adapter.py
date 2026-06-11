import json
import logging
import re

from ai.services.content_guard import ContentGuardError, check_user_content
from ai.services.credentials import AiConfig

logger = logging.getLogger(__name__)


class LlmAdapterError(Exception):
    pass


def _client(config: AiConfig):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LlmAdapterError("openai package is not installed") from exc

    return OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=60.0,
    )


def chat_completion(
    *,
    messages: list[dict],
    config: AiConfig,
    temperature: float = 0.3,
    content_guard: bool = True,
) -> str:
    if content_guard:
        for msg in messages:
            if msg.get("role") == "user":
                decision = check_user_content(msg.get("content", ""))
                if not decision.allowed:
                    raise ContentGuardError(decision)

    client = _client(config)
    response = client.chat.completions.create(
        model=config.chat_model,
        messages=messages,
        temperature=temperature,
    )
    content = response.choices[0].message.content
    if not content:
        raise LlmAdapterError("Empty LLM response")
    return content.strip()


def embed_texts(*, texts: list[str], config: AiConfig) -> list[list[float]]:
    if not texts:
        return []
    client = _client(config)
    response = client.embeddings.create(
        model=config.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


def parse_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)
