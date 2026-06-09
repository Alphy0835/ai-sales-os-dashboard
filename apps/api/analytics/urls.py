from django.urls import path

from analytics.views import EmployeeDashboardView, ManagerClientsView, ManagerDashboardView

urlpatterns = [
    path("manager/dashboard/", ManagerDashboardView.as_view(), name="manager-dashboard"),
    path("manager/clients/", ManagerClientsView.as_view(), name="manager-clients"),
    path("employee/dashboard/", EmployeeDashboardView.as_view(), name="employee-dashboard"),
]
