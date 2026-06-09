from collections import defaultdict

from accounts.models import User
from ai.models import AnalyticsReport, CustomReport, QualityCriterion
from integrations.models import Transcription


STAGE_LABELS = {
    QualityCriterion.FunnelStage.GREETING: "Приветствие",
    QualityCriterion.FunnelStage.DISCOVERY: "Выявление потребности",
    QualityCriterion.FunnelStage.PRESENTATION: "Презентация",
    QualityCriterion.FunnelStage.OBJECTIONS: "Работа с возражениями",
    QualityCriterion.FunnelStage.CLOSING: "Закрытие",
}


def _transcripts_queryset(*, tenant_id, workspace_id, employee_id=None):
    qs = Transcription.objects.filter(
        status=Transcription.Status.COMPLETED,
        recording__tenant_id=tenant_id,
        recording__workspace_id=workspace_id,
    ).select_related("recording", "recording__employee")
    if employee_id:
        qs = qs.filter(recording__employee_id=employee_id)
    return qs


def _score_criterion(criterion: QualityCriterion, texts: list[str]) -> dict:
    keywords = criterion.keyword_list()
    if not keywords:
        return {
            "criterion_id": str(criterion.id),
            "name": criterion.name,
            "stage": criterion.funnel_stage,
            "stage_label": STAGE_LABELS.get(criterion.funnel_stage, criterion.funnel_stage),
            "score": None,
            "matched_keywords": [],
            "available": False,
            "reason": "no_keywords",
        }

    matched = set()
    for text in texts:
        lower = text.lower()
        for kw in keywords:
            if kw in lower:
                matched.add(kw)

    score = round(len(matched) / len(keywords) * 100)
    return {
        "criterion_id": str(criterion.id),
        "name": criterion.name,
        "stage": criterion.funnel_stage,
        "stage_label": STAGE_LABELS.get(criterion.funnel_stage, criterion.funnel_stage),
        "score": score,
        "matched_keywords": sorted(matched),
        "available": True,
        "reason": None,
    }


def generate_analytics_report(
    *,
    actor: User,
    workspace,
    employee: User | None,
    template: str,
    custom_report: CustomReport | None = None,
) -> AnalyticsReport:
    criteria = list(
        QualityCriterion.objects.filter(tenant_id=actor.tenant_id, is_active=True).order_by("sort_order", "name")
    )
    if custom_report and custom_report.structured_query.get("focus_stages"):
        focus = set(custom_report.structured_query["focus_stages"])
        filtered = [c for c in criteria if c.funnel_stage in focus]
        if filtered:
            criteria = filtered
    transcripts = list(
        _transcripts_queryset(
            tenant_id=actor.tenant_id,
            workspace_id=workspace.id,
            employee_id=employee.id if employee else None,
        )
    )

    if not criteria:
        return AnalyticsReport.objects.create(
            tenant=actor.tenant,
            author=actor,
            workspace=workspace,
            employee=employee,
            template=template,
            status=AnalyticsReport.Status.FAILED,
            error_message="No quality criteria configured. Add criteria in Settings.",
            canvas={},
            custom_report=custom_report,
        )

    if not transcripts:
        return AnalyticsReport.objects.create(
            tenant=actor.tenant,
            author=actor,
            workspace=workspace,
            employee=employee,
            template=template,
            status=AnalyticsReport.Status.FAILED,
            error_message="No completed transcriptions for the selected scope.",
            canvas={},
            custom_report=custom_report,
        )

    texts = [t.text for t in transcripts if t.text]
    criterion_scores = [_score_criterion(c, texts) for c in criteria]

    stage_buckets: dict[str, list[int]] = defaultdict(list)
    for item in criterion_scores:
        if item["available"] and item["score"] is not None:
            stage_buckets[item["stage"]].append(item["score"])

    stages = []
    for stage, label in STAGE_LABELS.items():
        scores = stage_buckets.get(stage, [])
        avg = round(sum(scores) / len(scores)) if scores else None
        stages.append({"stage": stage, "label": label, "score": avg, "criteria_count": len(scores)})

    available_scores = [s["score"] for s in criterion_scores if s["available"] and s["score"] is not None]
    overall = round(sum(available_scores) / len(available_scores)) if available_scores else None

    weak = [s for s in criterion_scores if s["available"] and s["score"] is not None and s["score"] < 60]
    recommendations = []
    for item in sorted(weak, key=lambda x: x["score"])[:3]:
        recommendations.append(
            {
                "type": "review",
                "text": f"Разбор по критерию «{item['name']}» (оценка {item['score']}%)",
                "criterion_id": item["criterion_id"],
            }
        )

    target_name = employee.full_name if employee else workspace.name
    summary = f"Проанализировано записей: {len(transcripts)}. "
    if custom_report:
        summary = f"Кастомный отчёт «{custom_report.title}». " + summary
    if overall is not None:
        summary += f"Средняя оценка качества по критериям: {overall}%. "
    if recommendations:
        summary += "Рекомендуется провести разбор по слабым этапам воронки."
    else:
        summary += "Критичных просадок по критериям не выявлено."

    canvas = {
        "template": template,
        "custom_report_id": str(custom_report.id) if custom_report else None,
        "custom_report_title": custom_report.title if custom_report else None,
        "structured_query": custom_report.structured_query if custom_report else None,
        "overall_score": overall,
        "stages": stages,
        "criteria": criterion_scores,
        "dynamics": {
            "labels": [t.recording.client_name for t in transcripts[:5]],
            "values": [
                float(
                    sum(
                        s["score"]
                        for s in criterion_scores
                        if s["available"] and s["score"] is not None
                    )
                    / max(1, len([s for s in criterion_scores if s["available"]]))
                )
                for _ in transcripts[:5]
            ],
        },
        "recommendations": recommendations,
        "highlights": [
            {"type": "info", "text": f"Объект анализа: {target_name}"},
            {"type": "info", "text": f"Активных критериев: {len(criteria)}"},
        ],
    }
    if custom_report:
        canvas["highlights"].insert(0, {"type": "info", "text": custom_report.description[:120]})

    return AnalyticsReport.objects.create(
        tenant=actor.tenant,
        author=actor,
        workspace=workspace,
        employee=employee,
        template=template,
        status=AnalyticsReport.Status.COMPLETED,
        summary_text=summary,
        canvas=canvas,
        recordings_analyzed=len(transcripts),
        custom_report=custom_report,
    )
