from django.core.management.base import BaseCommand

from accounts.models import Tenant
from ai.models import QualityCriterion


DEFAULT_CRITERIA = [
    (
        "Приветствие и представление",
        QualityCriterion.FunnelStage.GREETING,
        "представился, здравствуйте, компания",
        10,
    ),
    (
        "Выявление потребности",
        QualityCriterion.FunnelStage.DISCOVERY,
        "потребность, уточнил, вопрос",
        20,
    ),
    (
        "Презентация решения",
        QualityCriterion.FunnelStage.PRESENTATION,
        "предложение, продукт, решение",
        30,
    ),
    (
        "Закрытие и next step",
        QualityCriterion.FunnelStage.CLOSING,
        "следующ, договор, встреч",
        40,
    ),
]


class Command(BaseCommand):
    help = "Seed demo quality criteria for AI analytics"

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(slug="demo").first()
        if not tenant:
            self.stdout.write(self.style.ERROR("Run seed_demo first"))
            return

        for name, stage, keywords, order in DEFAULT_CRITERIA:
            QualityCriterion.objects.update_or_create(
                tenant=tenant,
                name=name,
                defaults={
                    "funnel_stage": stage,
                    "keywords": keywords,
                    "description": f"Demo criterion: {name}",
                    "is_active": True,
                    "sort_order": order,
                },
            )

        self.stdout.write(self.style.SUCCESS("AI analytics demo criteria ready"))
