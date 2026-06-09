from django.core.management.base import BaseCommand

from accounts.models import Tenant, User, Workspace
from analytics.models import ClientToReview
from reviews.models import Review, ReviewTask


class Command(BaseCommand):
    help = "Seed demo review history and tasks"

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(slug="demo").first()
        if not tenant:
            self.stdout.write(self.style.ERROR("Run seed_demo first"))
            return

        moscow = Workspace.objects.get(tenant=tenant, name="ОП Москва")
        manager = User.objects.get(tenant=tenant, email="manager@demo.local")
        employee = User.objects.get(tenant=tenant, email="employee@demo.local")
        client = ClientToReview.objects.filter(
            tenant=tenant,
            employee=employee,
            client_name="ООО «Вектор»",
        ).first()

        review, created = Review.objects.update_or_create(
            tenant=tenant,
            workspace=moscow,
            employee=employee,
            author=manager,
            comment="Разбор по клиенту «Вектор»",
            defaults={
                "discussion": "Обсудили падение качества на этапе выявления потребности.",
                "client_to_review": client,
            },
        )
        if created:
            ReviewTask.objects.create(review=review, title="Переслушать 3 последних звонка")
            ReviewTask.objects.create(
                review=review,
                title="Обновить скрипт приветствия",
                status=ReviewTask.Status.IN_PROGRESS,
            )

        self.stdout.write(self.style.SUCCESS("Review demo data ready"))
