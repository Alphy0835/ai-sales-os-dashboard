from django.core.management.base import BaseCommand

from integrations.models import CrmLead, IntegrationSource


class Command(BaseCommand):
    help = "Delete cached CrmLead rows for Google Sheets integration sources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many rows would be deleted without deleting.",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            help="Optional tenant UUID to limit purge scope.",
        )

    def handle(self, *args, **options):
        source_qs = IntegrationSource.objects.filter(
            source_type=IntegrationSource.SourceType.CRM,
            config_json__provider="google_sheets",
        )
        if options.get("tenant"):
            source_qs = source_qs.filter(tenant_id=options["tenant"])

        source_ids = list(source_qs.values_list("id", flat=True))
        lead_qs = CrmLead.objects.filter(integration_source_id__in=source_ids)
        count = lead_qs.count()

        if options["dry_run"]:
            self.stdout.write(
                f"Would delete {count} CrmLead row(s) from {len(source_ids)} Google Sheets source(s)."
            )
            return

        deleted, _ = lead_qs.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted} CrmLead row(s) from {len(source_ids)} Google Sheets source(s)."
            )
        )
