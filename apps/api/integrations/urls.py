from django.urls import path

from integrations.views import (
    IntegrationSourceListView,
    IntegrationSourceSyncView,
    MetricsSummaryView,
    RecordingDetailView,
    RecordingListCreateView,
    RecordingTranscriptionView,
)

urlpatterns = [
    path("integrations/sources/", IntegrationSourceListView.as_view(), name="integration-sources"),
    path(
        "integrations/sources/<uuid:source_id>/sync/",
        IntegrationSourceSyncView.as_view(),
        name="integration-source-sync",
    ),
    path("integrations/metrics/", MetricsSummaryView.as_view(), name="integration-metrics"),
    path("integrations/recordings/", RecordingListCreateView.as_view(), name="integration-recordings"),
    path(
        "integrations/recordings/<uuid:recording_id>/",
        RecordingDetailView.as_view(),
        name="integration-recording-detail",
    ),
    path(
        "integrations/recordings/<uuid:recording_id>/transcription/",
        RecordingTranscriptionView.as_view(),
        name="integration-recording-transcription",
    ),
]
