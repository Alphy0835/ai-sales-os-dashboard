from django.core.management.base import BaseCommand

from ai.tasks import purge_expired_agent_chats


class Command(BaseCommand):
    help = "Delete agent chat sessions older than AGENT_CHAT_RETENTION_DAYS."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many sessions would be deleted without deleting.",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            from django.conf import settings
            from django.utils import timezone

            from ai.models import AgentChatSession

            retention_days = getattr(settings, "AGENT_CHAT_RETENTION_DAYS", 90)
            cutoff = timezone.now() - timezone.timedelta(days=retention_days)
            count = AgentChatSession.objects.filter(updated_at__lt=cutoff).count()
            self.stdout.write(f"Would delete {count} agent chat sessions (retention {retention_days} days).")
            return

        result = purge_expired_agent_chats()
        self.stdout.write(self.style.SUCCESS(f"Deleted {result['deleted']} agent chat sessions."))
