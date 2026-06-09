from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.services.audit import log_review_create
from reviews.models import ReviewTask
from reviews.serializers import (
    EmployeeTaskSerializer,
    ReviewCreateSerializer,
    ReviewListSerializer,
    TaskStatusUpdateSerializer,
)
from reviews.services.reviews import (
    can_edit_reviews,
    can_view_reviews,
    create_review,
    employee_tasks_queryset,
    resolve_client,
    resolve_review_employee,
    resolve_workspace,
    reviews_queryset,
    update_task_status,
)


def require_manager(user):
    if user.role != User.Role.MANAGER:
        raise PermissionDenied("Manager role required")


class ManagerReviewsView(APIView):
    def get(self, request):
        require_manager(request.user)
        if not can_view_reviews(request.user):
            raise PermissionDenied("Reviews view permission required")
        qs = reviews_queryset(
            request.user,
            workspace_id=request.query_params.get("workspace_id"),
            employee_id=request.query_params.get("employee_id"),
        )
        return Response(
            {
                "count": qs.count(),
                "results": ReviewListSerializer(qs, many=True).data,
            }
        )

    def post(self, request):
        require_manager(request.user)
        if not can_edit_reviews(request.user):
            raise PermissionDenied("Reviews edit permission required")

        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        employee = resolve_review_employee(request.user, str(data["employee_id"]))
        if not employee:
            raise ValidationError({"employee_id": "Employee not found or outside scope."})

        workspace = resolve_workspace(request.user, str(data["workspace_id"]))
        if not workspace:
            raise ValidationError({"workspace_id": "Workspace not found or outside scope."})

        if employee.workspace_id != workspace.id:
            raise ValidationError({"employee_id": "Employee does not belong to this workspace."})

        client = resolve_client(request.user, str(data["client_id"]) if data.get("client_id") else None)
        if data.get("client_id") and not client:
            raise ValidationError({"client_id": "Client not found or outside scope."})

        review = create_review(
            actor=request.user,
            employee=employee,
            workspace=workspace,
            comment=data["comment"],
            discussion=data.get("discussion", ""),
            client=client,
            task_titles=data.get("tasks") or [],
        )

        log_review_create(actor=request.user, target_user=employee, review_id=review.id)

        if client:
            client.status = client.Status.DONE
            client.save(update_fields=["status"])

        return Response(ReviewListSerializer(review).data, status=201)


class EmployeeTaskUpdateView(APIView):
    def patch(self, request, task_id):
        if request.user.role != User.Role.EMPLOYEE:
            raise PermissionDenied("Employee role required")

        try:
            task = employee_tasks_queryset(request.user).get(id=task_id)
        except ReviewTask.DoesNotExist:
            raise NotFound("Task not found.")

        serializer = TaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        update_task_status(task, serializer.validated_data["status"])
        task.refresh_from_db()
        return Response(EmployeeTaskSerializer(task).data)


def employee_tasks_payload(user: User):
    tasks = employee_tasks_queryset(user).order_by("-review__created_at", "created_at")
    return EmployeeTaskSerializer(tasks, many=True).data
