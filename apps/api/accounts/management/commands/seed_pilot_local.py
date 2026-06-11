from datetime import timedelta

import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.services.default_permissions import (
    EMPLOYEE_PERMISSIONS,
    MANAGER_PERMISSIONS,
    set_manager_scope,
    set_permissions,
)
from accounts.models import RegistrationInvite, Tenant, User, Workspace
from analytics.models import ClientToReview
from integrations.config_templates import GOOGLE_SHEETS_CONFIG_TEMPLATE
from integrations.models import CrmLead, IntegrationSource

PILOT_TENANT_SLUG = "pilot-local"
PILOT_WORKSPACE_NAME = "Pilot Office"
PILOT_INVITE_CODE = "PILOT-LOCAL-2026"
PILOT_SHEETS_SOURCE_NAME = "Pilot Google Sheets"

PILOT_LEADS = [
    {
        "external_lead_id": "PILOT-L-001",
        "client_name": "ООО «Север»",
        "phone": "+79990001101",
        "city": "Moscow",
        "communication_comment": "Needs follow-up call",
        "pipeline_stage": "Qualification",
        "status_stage": "open",
        "needs_review": True,
        "review_reason": "Needs follow-up call",
    },
    {
        "external_lead_id": "PILOT-L-002",
        "client_name": "АО «Вектор»",
        "phone": "+79990001102",
        "city": "Moscow",
        "communication_comment": "",
        "pipeline_stage": "Closing",
        "status_stage": "open",
        "needs_review": True,
        "review_reason": "Closing",
    },
    {
        "external_lead_id": "PILOT-L-003",
        "client_name": "ИП Петров",
        "phone": "+79990001103",
        "city": "Moscow",
        "communication_comment": "Active client with notes",
        "pipeline_stage": "Qualification",
        "status_stage": "open",
        "needs_review": False,
        "review_reason": "",
    },
    {
        "external_lead_id": "PILOT-L-004",
        "client_name": "ЗАО «Горизонт»",
        "phone": "+79990001104",
        "city": "Moscow",
        "communication_comment": "",
        "pipeline_stage": "Assigned",
        "status_stage": "assigned",
        "needs_review": True,
        "review_reason": "Assigned",
    },
    {
        "external_lead_id": "PILOT-L-005",
        "client_name": "ООО «Закрыто»",
        "phone": "+79990001105",
        "city": "Moscow",
        "communication_comment": "",
        "pipeline_stage": "Won",
        "status_stage": "done",
        "needs_review": False,
        "review_reason": "",
    },
]


class Command(BaseCommand):
    help = (
        "Seed pilot-local tenant for Gate A local testing. "
        "Run after migrations: python manage.py seed_pilot_local"
    )

    def handle(self, *args, **options):
        if not settings.DEBUG and os.environ.get("ALLOW_SEED_PILOT") != "1":
            raise CommandError(
                "Refusing seed_pilot_local in production without ALLOW_SEED_PILOT=1. "
                "Use integrator runbook for real tenants; never expose pilot1234 on public VPS."
            )

        tenant, _ = Tenant.objects.get_or_create(
            slug=PILOT_TENANT_SLUG,
            defaults={"name": "Pilot Local"},
        )
        workspace, _ = Workspace.objects.get_or_create(
            tenant=tenant,
            name=PILOT_WORKSPACE_NAME,
            defaults={"is_active": True},
        )

        manager, created = User.objects.get_or_create(
            tenant=tenant,
            email="pilot-mgr@local.test",
            defaults={
                "full_name": "Pilot Manager",
                "role": User.Role.MANAGER,
                "workspace": workspace,
                "is_active": True,
            },
        )
        if created:
            manager.set_password("pilot1234")
            manager.save()
        set_permissions(manager, MANAGER_PERMISSIONS)
        set_manager_scope(manager, [workspace])

        employee, created = User.objects.get_or_create(
            tenant=tenant,
            email="pilot-emp@local.test",
            defaults={
                "full_name": "Pilot Employee",
                "role": User.Role.EMPLOYEE,
                "workspace": workspace,
                "is_active": True,
            },
        )
        if created:
            employee.set_password("pilot1234")
            employee.save()
        set_permissions(employee, EMPLOYEE_PERMISSIONS)

        RegistrationInvite.objects.update_or_create(
            code=PILOT_INVITE_CODE,
            defaults={
                "tenant": tenant,
                "workspace": workspace,
                "role": User.Role.EMPLOYEE,
                "expires_at": timezone.now() + timedelta(days=365),
                "max_uses": 10,
            },
        )

        config_json = dict(GOOGLE_SHEETS_CONFIG_TEMPLATE)
        config_json["spreadsheet_id"] = config_json.get("spreadsheet_id") or "local-pilot-sheet-id"

        sheets_source, _ = IntegrationSource.objects.update_or_create(
            tenant=tenant,
            workspace=workspace,
            source_type=IntegrationSource.SourceType.CRM,
            name=PILOT_SHEETS_SOURCE_NAME,
            defaults={
                "status": IntegrationSource.Status.CONNECTED,
                "is_enabled": True,
                "config_json": config_json,
                "credentials_encrypted": "",
                "last_error": "",
                "last_sync_at": timezone.now(),
            },
        )

        now = timezone.now()
        review_count = 0
        for lead in PILOT_LEADS:
            CrmLead.objects.update_or_create(
                tenant=tenant,
                external_lead_id=lead["external_lead_id"],
                integration_source=sheets_source,
                defaults={
                    "workspace": workspace,
                    "employee": employee,
                    "client_name": lead["client_name"],
                    "phone": lead["phone"],
                    "city": lead["city"],
                    "communication_comment": lead["communication_comment"],
                    "pipeline_stage": lead["pipeline_stage"],
                    "status_stage": lead["status_stage"],
                    "manager_email": employee.email,
                    "supervisor_email": manager.email,
                    "synced_at": now,
                },
            )
            if lead["needs_review"]:
                ClientToReview.objects.update_or_create(
                    tenant=tenant,
                    workspace=workspace,
                    employee=employee,
                    client_external_id=lead["external_lead_id"],
                    defaults={
                        "client_name": lead["client_name"],
                        "reason": lead["review_reason"],
                        "priority": ClientToReview.Priority.MEDIUM,
                        "status": ClientToReview.Status.NEW,
                    },
                )
                review_count += 1

        self.stdout.write(self.style.SUCCESS("Pilot-local tenant ready (Gate A demo):"))
        self.stdout.write(f"  Tenant: {PILOT_TENANT_SLUG} / workspace «{PILOT_WORKSPACE_NAME}»")
        self.stdout.write("  pilot-mgr@local.test / pilot1234 (manager, full scope)")
        self.stdout.write("  pilot-emp@local.test / pilot1234 (employee)")
        self.stdout.write(f"  Registration invite: {PILOT_INVITE_CODE} (max 10 uses)")
        self.stdout.write(
            f"  Google Sheets CRM source: {sheets_source.name} "
            f"({review_count} clients to review, {len(PILOT_LEADS)} CRM leads)"
        )
