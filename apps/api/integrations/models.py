import uuid

from django.db import models


class IntegrationSource(models.Model):
    class SourceType(models.TextChoices):
        CRM = "crm", "CRM"
        TELEPHONY = "telephony", "Telephony"
        REPORTING = "reporting", "Reporting"

    class Status(models.TextChoices):
        CONNECTED = "connected", "Connected"
        DEGRADED = "degraded", "Degraded"
        DISCONNECTED = "disconnected", "Disconnected"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="integration_sources",
    )
    workspace = models.ForeignKey(
        "accounts.Workspace",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="integration_sources",
    )
    source_type = models.CharField(max_length=16, choices=SourceType.choices)
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DISCONNECTED,
    )
    is_enabled = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    external_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="External account id (e.g. amoCRM subdomain)",
    )
    credentials_encrypted = models.TextField(blank=True, default="")
    config_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["source_type", "name"]
        unique_together = [["tenant", "workspace", "source_type", "name"]]

    def __str__(self):
        return f"{self.source_type}:{self.name}"


class MetricSnapshot(models.Model):
    """Daily metric values pulled from integration sources."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="metric_snapshots",
    )
    workspace = models.ForeignKey(
        "accounts.Workspace",
        on_delete=models.CASCADE,
        related_name="metric_snapshots",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="metric_snapshots",
    )
    source = models.ForeignKey(
        IntegrationSource,
        on_delete=models.CASCADE,
        related_name="metric_snapshots",
    )
    metric_key = models.CharField(max_length=64)
    period_date = models.DateField()
    value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period_date", "metric_key"]
        unique_together = [["tenant", "user", "source", "metric_key", "period_date"]]

    def __str__(self):
        return f"{self.user.email}:{self.metric_key}@{self.period_date}"


class ConversationRecording(models.Model):
    class SourceKind(models.TextChoices):
        TELEPHONY = "telephony", "Telephony"
        MANUAL = "manual", "Manual upload"

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="recordings",
    )
    workspace = models.ForeignKey(
        "accounts.Workspace",
        on_delete=models.CASCADE,
        related_name="recordings",
    )
    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="recordings",
    )
    integration_source = models.ForeignKey(
        IntegrationSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recordings",
    )
    source_kind = models.CharField(max_length=16, choices=SourceKind.choices)
    client_name = models.CharField(max_length=255)
    client_external_id = models.CharField(max_length=128, blank=True, default="")
    audio_file = models.FileField(upload_to="recordings/%Y/%m/", blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.UPLOADED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client_name} ({self.employee.email})"


class Transcription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recording = models.OneToOneField(
        ConversationRecording,
        on_delete=models.CASCADE,
        related_name="transcription",
    )
    text = models.TextField(blank=True, default="")
    content_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True, default="")
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transcription:{self.recording_id}:{self.status}"


class CrmLead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="crm_leads",
    )
    workspace = models.ForeignKey(
        "accounts.Workspace",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="crm_leads",
    )
    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crm_leads",
    )
    integration_source = models.ForeignKey(
        IntegrationSource,
        on_delete=models.CASCADE,
        related_name="crm_leads",
    )
    external_lead_id = models.CharField(max_length=128)
    client_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=64, blank=True, default="")
    city = models.CharField(max_length=128, blank=True, default="")
    communication_comment = models.TextField(blank=True, default="")
    pipeline_stage = models.CharField(max_length=128, blank=True, default="")
    status_stage = models.CharField(max_length=128, blank=True, default="")
    recording_url = models.URLField(blank=True, default="")
    manager_email = models.CharField(max_length=255, blank=True, default="")
    supervisor_email = models.CharField(max_length=255, blank=True, default="")
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-synced_at"]
        unique_together = [["tenant", "external_lead_id", "integration_source"]]
        indexes = [
            models.Index(
                fields=["tenant", "employee"],
                name="crmlead_tenant_employee_idx",
            ),
            models.Index(
                fields=["tenant", "pipeline_stage"],
                name="crmlead_tenant_pipeline_idx",
            ),
            models.Index(
                fields=["tenant", "status_stage"],
                name="crmlead_tenant_status_idx",
            ),
            models.Index(
                fields=["tenant", "-synced_at"],
                name="crmlead_tenant_synced_idx",
            ),
        ]

    def __str__(self):
        return f"{self.client_name} ({self.external_lead_id})"
