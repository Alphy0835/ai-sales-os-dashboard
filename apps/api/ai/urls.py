from django.urls import path

from ai.views import (
    AnalyticsReportRunView,
    AnalyticsReportsView,
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
    path("manager/analytics/reports/", AnalyticsReportsView.as_view(), name="analytics-reports"),
    path("manager/analytics/reports/run/", AnalyticsReportRunView.as_view(), name="analytics-report-run"),
]
