from django.contrib import admin

from analytics.models import ClientToReview


@admin.register(ClientToReview)
class ClientToReviewAdmin(admin.ModelAdmin):
    list_display = ("client_name", "employee", "workspace", "priority", "status", "created_at")
    list_filter = ("priority", "status", "tenant")
