from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ModulePermission, User
from accounts.services.permissions import get_user_permissions
from analytics.serializers import ClientToReviewSerializer
from analytics.services.dashboard import build_manager_dashboard, clients_queryset


def require_dashboard_view(user):
    perms = get_user_permissions(user)
    if perms.get(ModulePermission.Module.DASHBOARD) == ModulePermission.Level.NONE:
        raise PermissionDenied("Dashboard view permission required")


def require_clients_or_dashboard_view(user):
    perms = get_user_permissions(user)
    if (
        perms.get(ModulePermission.Module.CLIENTS) != ModulePermission.Level.NONE
        or perms.get(ModulePermission.Module.DASHBOARD) != ModulePermission.Level.NONE
    ):
        return
    raise PermissionDenied("Clients or dashboard view permission required")


def require_manager(user):
    if user.role != User.Role.MANAGER:
        raise PermissionDenied("Manager role required")


class ManagerDashboardView(APIView):
    def get(self, request):
        require_dashboard_view(request.user)
        require_manager(request.user)
        data = build_manager_dashboard(
            actor=request.user,
            workspace_id=request.query_params.get("workspace_id"),
            user_id=request.query_params.get("user_id"),
        )
        if data is None:
            raise NotFound("Dashboard not available for requested scope")
        return Response(data)


class ManagerClientsView(APIView):
    def get(self, request):
        require_clients_or_dashboard_view(request.user)
        require_manager(request.user)
        qs = clients_queryset(
            request.user,
            workspace_id=request.query_params.get("workspace_id"),
            employee_id=request.query_params.get("employee_id"),
            status=request.query_params.get("status"),
        )
        return Response(
            {
                "count": qs.count(),
                "results": ClientToReviewSerializer(qs, many=True).data,
            }
        )


class EmployeeDashboardView(APIView):
    def get(self, request):
        require_dashboard_view(request.user)
        if request.user.role != User.Role.EMPLOYEE:
            raise PermissionDenied("Employee role required")
        data = build_manager_dashboard(
            actor=request.user,
            workspace_id=request.query_params.get("workspace_id"),
            user_id=request.query_params.get("user_id"),
        )
        if data is None:
            raise NotFound("Dashboard not available for requested scope")
        return Response(data)
