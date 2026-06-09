from django.core.management.base import BaseCommand

from accounts.models import Tenant
from ai.models import KnowledgeArticle


ARTICLES = [
    (
        "Продукт: CRM-модуль AI Sales OS",
        KnowledgeArticle.Category.PRODUCT,
        "crm, продукт, модуль, интеграция",
        KnowledgeArticle.AccessLevel.ALL,
        "CRM-модуль собирает сделки и активность менеджеров. Используйте для подготовки к звонку и контроля воронки.",
    ),
    (
        "Отработка: дорого",
        KnowledgeArticle.Category.OBJECTION,
        "дорого, цена, возражение, стоимость",
        KnowledgeArticle.AccessLevel.ALL,
        "На возражение «дорого» уточните бюджет, сравните с текущими потерями от просадки качества и предложите пилот.",
    ),
    (
        "Стратегия разбора ОП (только руководитель)",
        KnowledgeArticle.Category.CASE,
        "стратегия, разбор, руководитель, тактика",
        KnowledgeArticle.AccessLevel.MANAGER,
        "Руководителю: фокус на этапе выявления потребности и контроль 3 ключевых звонков в неделю.",
    ),
    (
        "Инфопovod: акция на CRM",
        KnowledgeArticle.Category.INFOPOVOD,
        "акция, crm, инфопovod, скидка",
        KnowledgeArticle.AccessLevel.EMPLOYEE,
        "До конца месяца скидка 15% на CRM-модуль для новых клиентов.",
    ),
]


class Command(BaseCommand):
    help = "Seed demo knowledge base articles"

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(slug="demo").first()
        if not tenant:
            self.stdout.write(self.style.ERROR("Run seed_demo first"))
            return

        for title, category, tags, access, content in ARTICLES:
            KnowledgeArticle.objects.update_or_create(
                tenant=tenant,
                title=title,
                defaults={
                    "category": category,
                    "tags": tags,
                    "access_level": access,
                    "content": content,
                    "is_active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Knowledge base demo ready"))
