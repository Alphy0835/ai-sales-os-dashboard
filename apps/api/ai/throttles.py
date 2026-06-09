from rest_framework.throttling import UserRateThrottle


class AgentRateThrottle(UserRateThrottle):
    scope = "agent"


class AnalyticsReportRunThrottle(UserRateThrottle):
    scope = "analytics_run"


class CustomReportThrottle(UserRateThrottle):
    scope = "custom_report"


class RecordingUploadThrottle(UserRateThrottle):
    scope = "recording_upload"
