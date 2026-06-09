from django.core.management.base import BaseCommand

from ai.models import KnowledgeArticle
from ai.tasks import embed_knowledge_article


class Command(BaseCommand):
    help = "Re-index knowledge base embeddings for all active articles."

    def handle(self, *args, **options):
        articles = KnowledgeArticle.objects.filter(is_active=True)
        count = 0
        for article in articles:
            embed_knowledge_article.delay(str(article.id))
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Queued {count} articles for embedding."))
