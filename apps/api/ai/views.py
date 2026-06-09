from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from ai.models import AgentChatSession, AnalyticsReport, CustomReport, KnowledgeArticle, QualityCriterion
from ai.serializers import (
    AgentChatRequestSerializer,
    AgentChatSessionSerializer,
    AnalyticsReportSerializer,
    CustomReportSerializer,
    KnowledgeArticleSerializer,
    QualityCriterionSerializer,
    ReportRunSerializer,
)
from ai.services.custom_reports import structure_custom_report
from ai.services.agent import chat_with_agent
from ai.services.knowledge import articles_editable_queryset, can_use_agent
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
            "workspace", "employee", "author", "custom_report"
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

        custom_report = None
        if data.get("custom_report_id"):
            try:
                custom_report = CustomReport.objects.get(
                    id=data["custom_report_id"],
                    tenant_id=request.user.tenant_id,
                    is_active=True,
                )
            except CustomReport.DoesNotExist:
                raise ValidationError({"custom_report_id": "Custom report not found."})

        template = data.get("template") or AnalyticsReport.Template.STANDARD_QUALITY
        if custom_report:
            template = AnalyticsReport.Template.CUSTOM

        report = generate_analytics_report(
            actor=request.user,
            workspace=workspace,
            employee=employee,
            template=template,
            custom_report=custom_report,
        )
        payload = AnalyticsReportSerializer(report).data
        if report.status == AnalyticsReport.Status.FAILED:
            return Response(payload, status=400)
        return Response(payload, status=201)


class KnowledgeArticleListCreateView(APIView):
    def get(self, request):
        require_manager(request.user)
        if not can_view_criteria(request.user):
            raise PermissionDenied("Settings view permission required")
        qs = articles_editable_queryset(request.user)
        return Response({"count": qs.count(), "results": KnowledgeArticleSerializer(qs, many=True).data})

    def post(self, request):
        require_manager(request.user)
        if not can_edit_criteria(request.user):
            raise PermissionDenied("Settings edit permission required")
        serializer = KnowledgeArticleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = serializer.save(tenant=request.user.tenant)
        return Response(KnowledgeArticleSerializer(article).data, status=201)


class KnowledgeArticleDetailView(APIView):
    def _get(self, request, article_id):
        try:
            return articles_editable_queryset(request.user).get(id=article_id)
        except KnowledgeArticle.DoesNotExist:
            raise NotFound("Article not found.")

    def patch(self, request, article_id):
        require_manager(request.user)
        if not can_edit_criteria(request.user):
            raise PermissionDenied("Settings edit permission required")
        article = self._get(request, article_id)
        serializer = KnowledgeArticleSerializer(article, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, article_id):
        require_manager(request.user)
        if not can_edit_criteria(request.user):
            raise PermissionDenied("Settings edit permission required")
        article = self._get(request, article_id)
        article.delete()
        return Response(status=204)


class ManagerAgentChatView(APIView):
    def post(self, request):
        require_manager(request.user)
        if not can_use_agent(request.user):
            raise PermissionDenied("Agent use permission required")
        serializer = AgentChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        session = chat_with_agent(
            actor=request.user,
            message=data["message"],
            session_id=str(data["session_id"]) if data.get("session_id") else None,
            client_name=data.get("client_name", ""),
            client_note=data.get("client_note", ""),
        )
        session = AgentChatSession.objects.prefetch_related("messages").get(id=session.id)
        return Response(AgentChatSessionSerializer(session).data)


class EmployeeAgentChatView(APIView):
    def post(self, request):
        if request.user.role != User.Role.EMPLOYEE:
            raise PermissionDenied("Employee role required")
        if not can_use_agent(request.user):
            raise PermissionDenied("Agent use permission required")
        serializer = AgentChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        session = chat_with_agent(
            actor=request.user,
            message=data["message"],
            session_id=str(data["session_id"]) if data.get("session_id") else None,
            client_name=data.get("client_name", ""),
            client_note=data.get("client_note", ""),
        )
        session = AgentChatSession.objects.prefetch_related("messages").get(id=session.id)
        return Response(AgentChatSessionSerializer(session).data)


class CustomReportListCreateView(APIView):
    def get(self, request):
        require_manager(request.user)
        if not can_view_criteria(request.user):
            raise PermissionDenied("Settings view permission required")
        qs = CustomReport.objects.filter(tenant_id=request.user.tenant_id).order_by("-updated_at")
        return Response({"count": qs.count(), "results": CustomReportSerializer(qs, many=True).data})

    def post(self, request):
        require_manager(request.user)
        if not can_edit_criteria(request.user):
            raise PermissionDenied("Settings edit permission required")
        serializer = CustomReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        structured = structure_custom_report(title=data["title"], description=data["description"])
        report = CustomReport.objects.create(
            tenant_id=request.user.tenant_id,
            author=request.user,
            title=data["title"],
            description=data["description"],
            structured_query=structured,
        )
        return Response(CustomReportSerializer(report).data, status=201)


class CustomReportDetailView(APIView):
    def _get(self, request, report_id):
        require_manager(request.user)
        if not can_view_criteria(request.user):
            raise PermissionDenied("Settings view permission required")
        try:
            return CustomReport.objects.get(id=report_id, tenant_id=request.user.tenant_id)
        except CustomReport.DoesNotExist:
            raise NotFound("Custom report not found")

    def get(self, request, report_id):
        return Response(CustomReportSerializer(self._get(request, report_id)).data)

    def patch(self, request, report_id):
        require_manager(request.user)
        if not can_edit_criteria(request.user):
            raise PermissionDenied("Settings edit permission required")
        report = self._get(request, report_id)
        serializer = CustomReportSerializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "title" in data or "description" in data:
            report.structured_query = structure_custom_report(
                title=data.get("title", report.title),
                description=data.get("description", report.description),
            )
        for field in ("title", "description", "is_active"):
            if field in data:
                setattr(report, field, data[field])
        report.save()
        return Response(CustomReportSerializer(report).data)

    def delete(self, request, report_id):
        require_manager(request.user)
        if not can_edit_criteria(request.user):
            raise PermissionDenied("Settings edit permission required")
        self._get(request, report_id).delete()
        return Response(status=204)
