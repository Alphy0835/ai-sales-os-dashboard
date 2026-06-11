"""Pre-LLM content policy: block personal topics and prompt-injection attempts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class ContentViolation(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    PERSONAL_TOPIC = "personal_topic"
    OFF_TOPIC = "off_topic"


BLOCK_MESSAGES: dict[ContentViolation, str] = {
    ContentViolation.PROMPT_INJECTION: (
        "Запрос отклонён: обнаружена попытка изменить правила ассистента. "
        "Задайте рабочий вопрос по продажам, клиентам или базе знаний."
    ),
    ContentViolation.PERSONAL_TOPIC: (
        "Я помогаю только по рабочим задачам отдела продаж. "
        "Личные темы (здоровье, семья, политика и т.п.) обсуждать не могу."
    ),
    ContentViolation.OFF_TOPIC: (
        "Запрос вне рабочей тематики. Спросите о клиентах, звонках, CRM, разборах или базе знаний."
    ),
}

# Prompt-injection / jailbreak (RU + EN)
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    for pattern in (
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(your\s+)?(rules|instructions|policy)",
        r"forget\s+(everything|all)\s+(you\s+)?(know|were\s+told)",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"act\s+as\s+(if\s+you\s+are\s+)?",
        r"new\s+system\s+prompt",
        r"reveal\s+(the\s+)?(system|hidden)\s+prompt",
        r"print\s+(your\s+)?(system|initial)\s+prompt",
        r"jailbreak",
        r"\bdan\s+mode\b",
        r"developer\s+mode\s+enabled",
        r"забудь\s+(все\s+)?инструкци",
        r"игнорируй\s+(все\s+)?(правила|инструкци)",
        r"нов(ая|ые)\s+роль",
        r"ты\s+теперь\s+",
        r"выведи\s+(системн(ый|ую)\s+)?промпт",
        r"покажи\s+(системн(ый|ую)\s+)?промпт",
        r"обойди\s+(ограничени|фильтр|защит)",
        r"\[system\]",
        r"<\s*/?\s*system\s*>",
        r"override\s+(safety|security|policy)",
    )
)

# Personal / sensitive off-work topics
_PERSONAL_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bличн(ая|ой|ые)\s+(жизн|дела|проблем)",
        r"\b(мо(й|я|и|их|ем|ей)|наш(а|и|ей))\s+(муж|жена|жён|супруг|парень|девушк|ребён|дет)",
        r"\b(развод|измен(а|ил)|расставан)",
        r"\b(депресси|тревог|паническ|психолог|психотерап|антидепресс)",
        r"\b(болезн|диагноз|рак\b|операци|беременност)",
        r"\b(политик|выбор(ы|ов)|партия\b|путин|байден|зеленск)",
        r"\b(религи|бог\b|церков|молитв|ислам|христ)",
        r"\b(секс|интим|порно)",
        r"\b(алкогол|наркот|курени)",
        r"\b(паспорт|снилс|инн\b)\s*(номер|данн)",
        r"\b(home\s+address|my\s+address)\b",
    )
)

# Clearly non-work entertainment (light filter; sales questions still pass)
_OFF_TOPIC_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(рецепт|как\s+готовить)\s",
        r"\b(фильм|сериал|аниме)\s+(посмотреть|совет)",
        r"\b(football|футбол)\s+(матч|счёт)",
        r"\b(cheat\s+code|чит\s+код)",
    )
)

# Delimiter breakout markers stripped before LLM packaging
_DELIMITER_MARKERS = ("[USER_INPUT]", "[/USER_INPUT]", "[SYSTEM]", "[/SYSTEM]")


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    violation: ContentViolation | None = None

    @property
    def block_message(self) -> str:
        if self.violation is None:
            return ""
        return BLOCK_MESSAGES[self.violation]


class ContentGuardError(Exception):
    def __init__(self, decision: GuardDecision):
        self.decision = decision
        super().__init__(decision.block_message)


def strip_delimiter_markers(value: str) -> str:
    text = value or ""
    for marker in _DELIMITER_MARKERS:
        text = text.replace(marker, "")
    return text.strip()


def _match_patterns(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def check_user_content(text: str) -> GuardDecision:
    """Scan raw user-originated text before any LLM call."""
    cleaned = strip_delimiter_markers(text)
    if not cleaned:
        return GuardDecision(allowed=True)

    normalized = re.sub(r"\s+", " ", cleaned)

    if _match_patterns(normalized, _INJECTION_PATTERNS):
        return GuardDecision(allowed=False, violation=ContentViolation.PROMPT_INJECTION)

    if _match_patterns(normalized, _PERSONAL_PATTERNS):
        return GuardDecision(allowed=False, violation=ContentViolation.PERSONAL_TOPIC)

    if _match_patterns(normalized, _OFF_TOPIC_PATTERNS):
        return GuardDecision(allowed=False, violation=ContentViolation.OFF_TOPIC)

    return GuardDecision(allowed=True)


def validate_agent_fields(*, message: str, client_name: str = "", client_note: str = "") -> GuardDecision:
    """Validate all free-text fields from the agent chat form."""
    for field in (message, client_name, client_note):
        decision = check_user_content(field)
        if not decision.allowed:
            return decision
    return GuardDecision(allowed=True)
