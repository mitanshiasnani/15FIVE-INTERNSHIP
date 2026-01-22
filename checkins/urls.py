from django.urls import path
from . import views

urlpatterns = [
    # ADMIN
    path("create/", views.create_checkin, name="create_checkin"),
    path("admin-panel/checkins/", views.admin_checkins_list, name="admin_checkins_list"),

    # 🔴 IMPORTANT: assignment_id (NOT form_id)
    path(
        "admin-panel/checkins/assignment/<int:assignment_id>/",
        views.admin_checkin_detail,
        name="admin_checkin_detail",
    ),

    # EMPLOYEE
    path("employee/", views.employee_checkins, name="employee_checkins"),
    path(
        "employee/<int:assignment_id>/",
        views.employee_checkin_form,
        name="employee_checkin_form",
    ),
]
