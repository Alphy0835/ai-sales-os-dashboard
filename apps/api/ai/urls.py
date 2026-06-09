from django.urls import path

from ai.views import (
    AnalyticsReportRunView,
    AnalyticsReportsView,
    CustomReportDetailView,
    CustomReportListCreateView,
    EmployeeAgentChatView,
    KnowledgeArticleDetailView,
    KnowledgeArticleListCreateView,
    ManagerAgentChatView,
    QualityCriteriaListCreateView,
    QualityCriterionDetailView,
)

urlpatterns = [
    path("manager/settings/quality-criteria/", QualityCriteriaListCreateView.as_view(), name="quality-criteria"),
    path(
        "manager/settings/quality-criteria/<uuid:criterion_id>/",
        QualityCriterionDetailView.as_view(),
        name="quality-criterion-detail",
    ),
    path("manager/settings/knowledge/", KnowledgeArticleListCreateView.as_view(), name="knowledge-articles"),
    path(
        "manager/settings/knowledge/<uuid:article_id>/",
        KnowledgeArticleDetailView.as_view(),
        name="knowledge-article-detail",
    ),
    path("manager/analytics/reports/", AnalyticsReportsView.as_view(), name="analytics-reports"),
    path("manager/analytics/reports/run/", AnalyticsReportRunView.as_view(), name="analytics-report-run"),
    path("manager/settings/custom-reports/", CustomReportListCreateView.as_view(), name="custom-reports"),
    path(
        "manager/settings/custom-reports/<uuid:report_id>/",
        CustomReportDetailView.as_view(),
        name="custom-report-detail",
    ),
    path("manager/agent/chat/", ManagerAgentChatView.as_view(), name="manager-agent-chat"),
    path("employee/agent/chat/", EmployeeAgentChatView.as_view(), name="employee-agent-chat"),
]
