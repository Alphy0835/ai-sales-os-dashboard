from django.core.management.base import BaseCommand

from accounts.models import Tenant, User
from ai.models import CustomReport
from ai.services.custom_reports import structure_custom_report

DEFAULT_REPORTS = [
    (
        "Фокус на закрытие",
        "Отчёт по качеству закрытия сделок, договорённостям и следующим шагам",
    ),
    (
        "Выявление потребностей",
        "Анализ этапа discovery: вопросы к клиенту и выявление потребности",
    ),
]


class Command(BaseCommand):
    help = "Seed demo custom AI reports"

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(slug="demo").first()
        if not tenant:
            self.stdout.write(self.style.ERROR("Run seed_demo first"))
            return

        author = User.objects.filter(tenant=tenant, email="manager@demo.local").first()
        if not author:
            self.stdout.write(self.style.ERROR("Demo manager not found"))
            return

        for title, description in DEFAULT_REPORTS:
            structured = structure_custom_report(title=title, description=description)
            CustomReport.objects.update_or_create(
                tenant=tenant,
                title=title,
                defaults={
                    "author": author,
                    "description": description,
                    "structured_query": structured,
                    "is_active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Custom AI reports demo data ready"))
