from accounts.models import User
from accounts.services.audit import log_permission_change
from accounts.services.scope import user_in_scope
from ai.models import KnowledgeArticle, KnowledgeArticleGrant
from ai.services.knowledge import article_accessible, articles_editable_queryset


class KnowledgeGrantError(Exception):
    def __init__(self, message: str, code: str = "error"):
        super().__init__(message)
        self.code = code


def list_knowledge_grants(*, grantor: User, target: User) -> list[dict]:
    articles = list(articles_editable_queryset(grantor).filter(is_active=True).order_by("title"))
    grants = {
        str(g.article_id): g
        for g in KnowledgeArticleGrant.objects.filter(
            tenant_id=grantor.tenant_id,
            user=target,
        )
    }
    results = []
    for article in articles:
        grant = grants.get(str(article.id))
        results.append(
            {
                "article_id": str(article.id),
                "title": article.title,
                "access_level": article.access_level,
                "base_accessible": article_accessible(target, article),
                "is_allowed": grant.is_allowed if grant else None,
                "grantor_can_assign": article_accessible(grantor, article),
            }
        )
    return results


def update_knowledge_grants(
    *,
    grantor: User,
    target: User,
    grants: list[dict],
    ip_address: str | None = None,
) -> list[dict]:
    if not user_in_scope(grantor, target):
        raise KnowledgeGrantError("User is outside your scope", code="scope_denied")

    updated = 0
    for item in grants:
        article_id = item.get("article_id")
        is_allowed = item.get("is_allowed")
        if article_id is None or is_allowed is None:
            continue

        try:
            article = articles_editable_queryset(grantor).get(id=article_id, is_active=True)
        except KnowledgeArticle.DoesNotExist:
            raise KnowledgeGrantError(f"Article not found: {article_id}", code="not_found")

        if not article_accessible(grantor, article):
            raise KnowledgeGrantError(
                f"Cannot grant access to article you cannot access: {article.title}",
                code="ceiling_violation",
            )

        KnowledgeArticleGrant.objects.update_or_create(
            tenant_id=grantor.tenant_id,
            user=target,
            article=article,
            defaults={"is_allowed": bool(is_allowed)},
        )
        updated += 1

    if updated:
        log_permission_change(
            actor=grantor,
            target_user=target,
            module="knowledge",
            old_level="",
            new_level=f"grants_updated:{updated}",
            ip_address=ip_address,
        )

    return list_knowledge_grants(grantor=grantor, target=target)
