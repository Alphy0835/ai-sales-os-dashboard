import uuid

from django.db import models


class ClientToReview(models.Model):
    class Priority(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="clients_to_review",
    )
    workspace = models.ForeignKey(
        "accounts.Workspace",
        on_delete=models.CASCADE,
        related_name="clients_to_review",
    )
    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="clients_to_review",
    )
    client_name = models.CharField(max_length=255)
    client_external_id = models.CharField(max_length=128, blank=True, default="")
    reason = models.TextField()
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-priority", "-created_at"]

    def __str__(self):
        return f"{self.client_name} → {self.employee.email}"
