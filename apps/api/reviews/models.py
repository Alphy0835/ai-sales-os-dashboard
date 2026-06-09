import uuid

from django.db import models


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE, related_name="reviews")
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, related_name="reviews")
    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="reviews_received",
    )
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="reviews_authored",
    )
    client_to_review = models.ForeignKey(
        "analytics.ClientToReview",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    comment = models.TextField()
    discussion = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review {self.employee.email} @ {self.created_at:%Y-%m-%d}"


class ReviewTask(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=500)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.title
