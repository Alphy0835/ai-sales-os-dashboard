from django.utils import timezone

from accounts.models import ModulePermission, User, Workspace
from accounts.services.scope import get_accessible_users, get_scoped_workspaces, user_in_scope
from analytics.models import ClientToReview
from reviews.models import Review, ReviewTask


def reviews_permission_level(user) -> str:
    from accounts.services.permissions import get_user_permissions

    return get_user_permissions(user).get(ModulePermission.Module.REVIEWS, ModulePermission.Level.NONE)


def can_view_reviews(user) -> bool:
    return reviews_permission_level(user) != ModulePermission.Level.NONE


def can_edit_reviews(user) -> bool:
    return reviews_permission_level(user) == ModulePermission.Level.EDIT


def reviews_queryset(actor: User, *, workspace_id: str | None = None, employee_id: str | None = None):
    qs = Review.objects.filter(tenant_id=actor.tenant_id).select_related(
        "employee",
        "author",
        "workspace",
        "client_to_review",
    ).prefetch_related("tasks")

    if actor.role == User.Role.EMPLOYEE:
        return qs.filter(employee=actor)

    employee_ids = [u.id for u in get_accessible_users(actor) if u.role == User.Role.EMPLOYEE]
    qs = qs.filter(employee_id__in=employee_ids)

    if workspace_id:
        qs = qs.filter(workspace_id=workspace_id)
    if employee_id:
        qs = qs.filter(employee_id=employee_id)
    return qs


def employee_tasks_queryset(employee: User):
    return ReviewTask.objects.filter(
        review__tenant_id=employee.tenant_id,
        review__employee=employee,
    ).select_related("review", "review__author", "review__workspace")


def resolve_review_employee(actor: User, employee_id: str) -> User | None:
    try:
        employee = User.objects.get(id=employee_id, tenant_id=actor.tenant_id, is_active=True)
    except User.DoesNotExist:
        return None
    if employee.role != User.Role.EMPLOYEE or not user_in_scope(actor, employee):
        return None
    return employee


def resolve_workspace(actor: User, workspace_id: str) -> Workspace | None:
    try:
        workspace = Workspace.objects.get(id=workspace_id, tenant_id=actor.tenant_id, is_active=True)
    except Workspace.DoesNotExist:
        return None
    scoped_ids = {ws.id for ws in get_scoped_workspaces(actor)}
    if workspace.id not in scoped_ids:
        return None
    return workspace


def resolve_client(actor: User, client_id: str | None) -> ClientToReview | None:
    if not client_id:
        return None
    try:
        client = ClientToReview.objects.select_related("employee").get(
            id=client_id,
            tenant_id=actor.tenant_id,
        )
    except ClientToReview.DoesNotExist:
        return None
    if not user_in_scope(actor, client.employee):
        return None
    return client


def create_review(
    *,
    actor: User,
    employee: User,
    workspace: Workspace,
    comment: str,
    discussion: str = "",
    client: ClientToReview | None = None,
    task_titles: list[str],
) -> Review:
    review = Review.objects.create(
        tenant=actor.tenant,
        workspace=workspace,
        employee=employee,
        author=actor,
        client_to_review=client,
        comment=comment,
        discussion=discussion,
    )
    for title in task_titles:
        title = title.strip()
        if title:
            ReviewTask.objects.create(review=review, title=title)
    return review


def update_task_status(task: ReviewTask, new_status: str) -> ReviewTask:
    task.status = new_status
    if new_status == ReviewTask.Status.DONE:
        task.completed_at = timezone.now()
    else:
        task.completed_at = None
    task.save(update_fields=["status", "completed_at", "updated_at"])
    return task
