from ai.models import QualityCriterion


STAGE_KEYWORDS = {
    QualityCriterion.FunnelStage.GREETING: ["привет", "greeting", "представ"],
    QualityCriterion.FunnelStage.DISCOVERY: ["потребност", "discovery", "выявлен", "вопрос"],
    QualityCriterion.FunnelStage.PRESENTATION: ["презентац", "presentation", "продукт", "решение"],
    QualityCriterion.FunnelStage.OBJECTIONS: ["возраж", "objection", "дорого", "сомнен"],
    QualityCriterion.FunnelStage.CLOSING: ["закрыт", "closing", "следующ", "договор", "встреч"],
}


def structure_custom_report(*, title: str, description: str) -> dict:
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
