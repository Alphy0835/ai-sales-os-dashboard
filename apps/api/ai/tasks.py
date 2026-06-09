import logging

from celery import shared_task
from django.db import connection

from ai.models import KnowledgeArticle
from ai.services.credentials import llm_available, resolve_ai_config
from ai.services.llm_adapter import LlmAdapterError, embed_texts

logger = logging.getLogger(__name__)


@shared_task(name="ai.embed_knowledge_article")
def embed_knowledge_article(article_id: str) -> None:
    if connection.vendor != "postgresql":
        return

    try:
        article = KnowledgeArticle.objects.get(id=article_id, is_active=True)
    except KnowledgeArticle.DoesNotExist:
        return

    content_hash = article.compute_content_hash()
    if article.content_hash == content_hash and article.embedding is not None:
        return

    actor = article.tenant.users.filter(role="manager", is_active=True).first()
    if actor is None:
        actor = article.tenant.users.filter(is_active=True).first()
    if actor is None:
        return

    config = resolve_ai_config(actor)
    if not llm_available(config):
        return

    try:
        vectors = embed_texts(texts=[article.embed_text()], config=config)
    except LlmAdapterError as exc:
        logger.warning("Embedding failed for article %s: %s", article_id, exc)
        return

    if not vectors:
        return

    article.embedding = vectors[0]
    article.content_hash = content_hash
    article.save(update_fields=["embedding", "content_hash", "updated_at"])
