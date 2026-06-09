from django.urls import path

from reviews.views import EmployeeTaskUpdateView, ManagerReviewsView

urlpatterns = [
    path("manager/reviews/", ManagerReviewsView.as_view(), name="manager-reviews"),
    path("employee/tasks/<uuid:task_id>/", EmployeeTaskUpdateView.as_view(), name="employee-task-update"),
]
