from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from ai.models import AnalyticsReport, QualityCriterion
from ai.serializers import AnalyticsReportSerializer, QualityCriterionSerializer, ReportRunSerializer
from ai.services.permissions import (
    can_edit_criteria,
    can_run_reports,
    can_view_criteria,
    can_view_reports,
    criteria_queryset,
    resolve_report_scope,
)
from ai.services.reports import generate_analytics_report


def require_manager(user):
    if user.role != User.Role.MANAGER:
        raise PermissionDenied("Manager role required")


class QualityCriteriaListCreateView(APIView):
    def get(self, request):
        require_manager(request.user)
        if not can_view_criteria(request.user):
            raise PermissionDenied("Settings view permission required")
        qs = criteria_queryset(request.user)
        return Response({"count": qs.count(), "results": QualityCriterionSerializer(qs, many=True).data})

    def post(self, request):
        require_manager(request.user)
        if not can_edit_criteria(request.user):
            raise PermissionDenied("Settings edit permission required")
        serializer = QualityCriterionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        criterion = serializer.save(tenant=request.user.tenant)
        return Response(QualityCriterionSerializer(criterion).data, status=201)


class QualityCriterionDetailView(APIView):
    def _get(self, request, criterion_id):
        try:
            return criteria_queryset(request.user).get(id=criterion_id)
        except QualityCriterion.DoesNotExist:
            raise NotFound("Criterion not found.")

    def patch(self, request, criterion_id):
        require_manager(request.user)
        if not can_edit_criteria(request.user):
            raise PermissionDenied("Settings edit permission required")
        criterion = self._get(request, criterion_id)
        serializer = QualityCriterionSerializer(criterion, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, criterion_id):
        require_manager(request.user)
        if not can_edit_criteria(request.user):
            raise PermissionDenied("Settings edit permission required")
        criterion = self._get(request, criterion_id)
        criterion.delete()
        return Response(status=204)


class AnalyticsReportsView(APIView):
    def get(self, request):
        require_manager(request.user)
        if not can_view_reports(request.user):
            raise PermissionDenied("Analytics view permission required")
        qs = AnalyticsReport.objects.filter(tenant_id=request.user.tenant_id).select_related(
            "workspace", "employee", "author"
        )[:50]
        return Response({"count": qs.count(), "results": AnalyticsReportSerializer(qs, many=True).data})


class AnalyticsReportRunView(APIView):
    def post(self, request):
        require_manager(request.user)
        if not can_run_reports(request.user):
            raise PermissionDenied("Analytics run permission required")

        serializer = ReportRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        workspace, employee, err = resolve_report_scope(
            request.user,
            workspace_id=str(data["workspace_id"]),
            employee_id=str(data["employee_id"]) if data.get("employee_id") else None,
        )
        if err:
            raise ValidationError(err)

        report = generate_analytics_report(
            actor=request.user,
            workspace=workspace,
            employee=employee,
            template=data["template"],
        )
        payload = AnalyticsReportSerializer(report).data
        if report.status == AnalyticsReport.Status.FAILED:
            return Response(payload, status=400)
        return Response(payload, status=201)
