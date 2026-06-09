from django.core.management.base import BaseCommand

from accounts.models import Tenant, User, Workspace
from analytics.models import ClientToReview


class Command(BaseCommand):
    help = "Seed demo clients to review for manager dashboard"

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(slug="demo").first()
        if not tenant:
            self.stdout.write(self.style.ERROR("Run seed_demo first"))
            return

        moscow = Workspace.objects.get(tenant=tenant, name="ОП Москва")
        employee = User.objects.get(tenant=tenant, email="employee@demo.local")

        clients = [
            ("ООО «Вектор»", "Качество 68% · 3 звонка за неделю", ClientToReview.Priority.HIGH),
            ("АО «Север»", "Нет касаний 5 дней", ClientToReview.Priority.MEDIUM),
            ("ИП Петров", "Риск по воронке · низкая конверсия", ClientToReview.Priority.HIGH),
        ]
        for name, reason, priority in clients:
            ClientToReview.objects.update_or_create(
                tenant=tenant,
                workspace=moscow,
                employee=employee,
                client_name=name,
                defaults={"reason": reason, "priority": priority, "status": ClientToReview.Status.NEW},
            )

        self.stdout.write(self.style.SUCCESS("Dashboard demo clients ready"))
