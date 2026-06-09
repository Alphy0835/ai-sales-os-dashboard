from accounts.models import ModulePermission, User
from ai.models import KnowledgeArticle


def can_use_agent(user) -> bool:
    from accounts.services.permissions import get_user_permissions

    return get_user_permissions(user).get(ModulePermission.Module.AGENT, ModulePermission.Level.NONE) == ModulePermission.Level.USE


def articles_queryset(actor: User):
    return KnowledgeArticle.objects.filter(tenant_id=actor.tenant_id, is_active=True)


def articles_editable_queryset(actor: User):
    return KnowledgeArticle.objects.filter(tenant_id=actor.tenant_id)


def article_accessible(actor: User, article: KnowledgeArticle) -> bool:
    if article.access_level == KnowledgeArticle.AccessLevel.ALL:
        return True
    if article.access_level == KnowledgeArticle.AccessLevel.MANAGER:
        return actor.role == User.Role.MANAGER
    if article.access_level == KnowledgeArticle.AccessLevel.EMPLOYEE:
        return actor.role == User.Role.EMPLOYEE
    return False


def search_knowledge(actor: User, query: str, *, include_restricted_hint: bool = False) -> tuple[list[KnowledgeArticle], list[KnowledgeArticle]]:
    """Return (accessible matches, restricted matches that would have matched)."""
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
