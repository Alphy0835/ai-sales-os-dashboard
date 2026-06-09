import uuid

from django.db import models


class QualityCriterion(models.Model):
    class FunnelStage(models.TextChoices):
        GREETING = "greeting", "Greeting"
        DISCOVERY = "discovery", "Discovery"
        PRESENTATION = "presentation", "Presentation"
        OBJECTIONS = "objections", "Objections"
        CLOSING = "closing", "Closing"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE, related_name="quality_criteria")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    funnel_stage = models.CharField(max_length=32, choices=FunnelStage.choices)
    keywords = models.TextField(
        blank=True,
        default="",
        help_text="Comma-separated keywords matched in transcripts (MVP rule-based scoring)",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "quality criteria"

    def __str__(self):
        return self.name

    def keyword_list(self) -> list[str]:
        return [k.strip().lower() for k in self.keywords.split(",") if k.strip()]


class AnalyticsReport(models.Model):
    class Template(models.TextChoices):
        STANDARD_QUALITY = "standard_quality", "Standard quality"
        FUNNEL_DYNAMICS = "funnel_dynamics", "Funnel dynamics"

    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE, related_name="analytics_reports")
    author = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="analytics_reports_authored")
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, related_name="analytics_reports")
    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="analytics_reports_subject",
    )
    template = models.CharField(max_length=32, choices=Template.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.COMPLETED)
    summary_text = models.TextField(blank=True, default="")
    canvas = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")
    recordings_analyzed = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        target = self.employee.full_name if self.employee_id else self.workspace.name
        return f"{self.template} — {target}"
