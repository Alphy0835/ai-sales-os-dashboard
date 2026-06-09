from django.core.management.base import BaseCommand

from integrations.tasks import purge_expired_transcripts


class Command(BaseCommand):
    help = "Delete conversation recordings and transcriptions older than TRANSCRIPT_RETENTION_DAYS."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many records would be deleted without deleting.",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            from django.conf import settings
            from django.utils import timezone

            from integrations.models import ConversationRecording

            retention_days = getattr(settings, "TRANSCRIPT_RETENTION_DAYS", 90)
            cutoff = timezone.now() - timezone.timedelta(days=retention_days)
            count = ConversationRecording.objects.filter(created_at__lt=cutoff).count()
            self.stdout.write(f"Would delete {count} recordings (retention {retention_days} days).")
            return

        result = purge_expired_transcripts()
        self.stdout.write(self.style.SUCCESS(f"Deleted {result['deleted']} recordings."))
