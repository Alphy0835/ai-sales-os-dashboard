from accounts.models import ModulePermission, User
from accounts.services.permissions import get_user_permissions
from ai.models import KnowledgeArticle, KnowledgeArticleGrant


def can_use_agent(user) -> bool:
    return get_user_permissions(user).get(ModulePermission.Module.AGENT, ModulePermission.Level.NONE) == ModulePermission.Level.USE


def articles_queryset(actor: User):
    return KnowledgeArticle.objects.filter(tenant_id=actor.tenant_id, is_active=True)


def articles_editable_queryset(actor: User):
    return KnowledgeArticle.objects.filter(tenant_id=actor.tenant_id)


def _base_accessible(actor: User, article: KnowledgeArticle) -> bool:
    if article.access_level == KnowledgeArticle.AccessLevel.ALL:
        return True
    if article.access_level == KnowledgeArticle.AccessLevel.MANAGER:
        return actor.role == User.Role.MANAGER
    if article.access_level == KnowledgeArticle.AccessLevel.EMPLOYEE:
        return actor.role == User.Role.EMPLOYEE
    return False


def article_accessible(actor: User, article: KnowledgeArticle) -> bool:
    grant = KnowledgeArticleGrant.objects.filter(
        user_id=actor.id,
        article_id=article.id,
        tenant_id=actor.tenant_id,
    ).first()
    if grant is not None:
        return grant.is_allowed
    return _base_accessible(actor, article)


def _keyword_search(actor: User, query: str, *, include_restricted_hint: bool = False):
    tokens = [t.strip().lower() for t in query.split() if len(t.strip()) > 2]
    if not tokens:
        tokens = [query.strip().lower()] if query.strip() else []

    accessible: list[KnowledgeArticle] = []
    restricted: list[KnowledgeArticle] = []

    for article in articles_queryset(actor):
        haystack = " ".join([article.title, article.content, article.tags, article.category]).lower()
        if not tokens or any(tok in haystack for tok in tokens):
            if article_accessible(actor, article):
                accessible.append(article)
            elif include_restricted_hint:
                restricted.append(article)

    return accessible[:5], restricted[:3]


def _vector_search(actor: User, query: str, *, include_restricted_hint: bool = False):
    from django.db import connection

    from pgvector.django import CosineDistance

    from ai.services.credentials import llm_available, resolve_ai_config
    from ai.services.llm_adapter import LlmAdapterError, embed_texts

    if connection.vendor != "postgresql":
        return None

    config = resolve_ai_config(actor)
    if not llm_available(config):
        return None

    try:
        query_vectors = embed_texts(texts=[query], config=config)
    except LlmAdapterError:
        return None

    if not query_vectors:
        return None

    qs = (
        articles_queryset(actor)
        .exclude(embedding__isnull=True)
        .annotate(distance=CosineDistance("embedding", query_vectors[0]))
        .order_by("distance")[:15]
    )

    accessible: list[KnowledgeArticle] = []
    restricted: list[KnowledgeArticle] = []
    for article in qs:
        if article_accessible(actor, article):
            accessible.append(article)
        elif include_restricted_hint:
            restricted.append(article)
        if len(accessible) >= 5 and (not include_restricted_hint or len(restricted) >= 3):
            break

    return accessible[:5], restricted[:3]


def search_knowledge(actor: User, query: str, *, include_restricted_hint: bool = False) -> tuple[list[KnowledgeArticle], list[KnowledgeArticle]]:
    """Return (accessible matches, restricted matches that would have matched)."""
    if query.strip():
        vector_result = _vector_search(actor, query, include_restricted_hint=include_restricted_hint)
        if vector_result is not None and vector_result[0]:
            return vector_result

    return _keyword_search(actor, query, include_restricted_hint=include_restricted_hint)
