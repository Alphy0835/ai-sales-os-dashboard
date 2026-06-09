import logging

from accounts.models import User
from ai.models import QualityCriterion
from ai.services.credentials import llm_available, resolve_ai_config
from ai.services.llm_adapter import LlmAdapterError, chat_completion, parse_json_object

logger = logging.getLogger(__name__)

STAGE_KEYWORDS = {
    QualityCriterion.FunnelStage.GREETING: ["привет", "greeting", "представ"],
    QualityCriterion.FunnelStage.DISCOVERY: ["потребност", "discovery", "выявлен", "вопрос"],
    QualityCriterion.FunnelStage.PRESENTATION: ["презентац", "presentation", "продукт", "решение"],
    QualityCriterion.FunnelStage.OBJECTIONS: ["возраж", "objection", "дорого", "сомнен"],
    QualityCriterion.FunnelStage.CLOSING: ["закрыт", "closing", "следующ", "договор", "встреч"],
}

VALID_STAGES = {choice.value for choice in QualityCriterion.FunnelStage}


def _rule_based_structure(*, title: str, description: str) -> dict:
    text = f"{title} {description}".lower()
    focus_stages = [
        stage
        for stage, keywords in STAGE_KEYWORDS.items()
        if any(kw in text for kw in keywords)
    ]
    focus_keywords = [word for word in text.replace(",", " ").split() if len(word) > 4][:12]
    return {
        "title": title,
        "description": description,
        "focus_stages": focus_stages,
        "focus_keywords": focus_keywords,
        "engine": "rule_based_v1",
    }


def structure_custom_report(*, title: str, description: str, actor: User | None = None) -> dict:
    if actor is not None:
        config = resolve_ai_config(actor)
        if llm_available(config):
            stages_list = ", ".join(VALID_STAGES)
            prompt = (
                f"Структурируй описание кастомного отчёта продаж.\n"
                f"Название: {title}\n"
                f"Описание: {description}\n"
                f"Верни JSON с ключами: focus_stages (список из: {stages_list}), "
                f"focus_keywords (список строк, до 12). Без markdown."
            )
            try:
                raw = chat_completion(
                    messages=[
                        {"role": "system", "content": "Отвечай только валидным JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    config=config,
                )
                parsed = parse_json_object(raw)
                focus_stages = [s for s in parsed.get("focus_stages", []) if s in VALID_STAGES]
                focus_keywords = [str(k)[:64] for k in parsed.get("focus_keywords", [])[:12]]
                return {
                    "title": title,
                    "description": description,
                    "focus_stages": focus_stages,
                    "focus_keywords": focus_keywords,
                    "engine": "llm_v1",
                }
            except (LlmAdapterError, ValueError, KeyError) as exc:
                logger.warning("LLM custom report fallback: %s", exc)

    return _rule_based_structure(title=title, description=description)
