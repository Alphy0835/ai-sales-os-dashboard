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
        CUSTOM = "custom", "Custom"

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
    custom_report = models.ForeignKey(
        "CustomReport",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="runs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        target = self.employee.full_name if self.employee_id else self.workspace.name
        return f"{self.template} — {target}"


class KnowledgeArticle(models.Model):
    class Category(models.TextChoices):
        PRODUCT = "product", "Product"
        OBJECTION = "objection", "Objection handling"
        INFOPOVOD = "infopovod", "Infopovod"
        CASE = "case", "Case study"
        OTHER = "other", "Other"

    class AccessLevel(models.TextChoices):
        ALL = "all", "All users"
        MANAGER = "manager", "Managers only"
        EMPLOYEE = "employee", "Employees only"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE, related_name="knowledge_articles")
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=Category.choices, default=Category.OTHER)
    content = models.TextField()
    tags = models.CharField(max_length=500, blank=True, default="")
    access_level = models.CharField(max_length=16, choices=AccessLevel.choices, default=AccessLevel.ALL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "title"]

    def __str__(self):
        return self.title

    def tag_list(self) -> list[str]:
        return [t.strip().lower() for t in self.tags.split(",") if t.strip()]


class AgentChatSession(models.Model):
    class AgentRole(models.TextChoices):
        MANAGER = "manager", "Manager"
        EMPLOYEE = "employee", "Employee"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE, related_name="agent_sessions")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="agent_sessions")
    agent_role = models.CharField(max_length=16, choices=AgentRole.choices)
    client_name = models.CharField(max_length=255, blank=True, default="")
    client_note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class AgentChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AgentChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class CustomReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE, related_name="custom_reports")
    author = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="custom_reports_authored")
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Natural language report description from manager")
    structured_query = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title
