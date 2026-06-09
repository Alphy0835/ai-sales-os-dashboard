from django.contrib import admin

from reviews.models import Review, ReviewTask


class ReviewTaskInline(admin.TabularInline):
    model = ReviewTask
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("employee", "author", "workspace", "created_at")
    list_filter = ("workspace",)
    inlines = [ReviewTaskInline]


@admin.register(ReviewTask)
class ReviewTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "review", "status", "updated_at")
    list_filter = ("status",)
