from django.urls import path
from . import views

urlpatterns = [
    # MODULE 4
    path("checkins/create/", views.create_checkin, name="create_checkin"),

    # MODULE 5 (Employee)
    path("employee/checkins/", views.employee_checkins, name="employee_checkins"),
    path(
        "employee/checkins/<int:assignment_id>/submit/",
        views.employee_checkin_form,
        name="employee_checkin_form",
    ),

    # MODULE 6 (Admin Panel – NOT Django Admin)
    path(
        "admin-panel/checkins/",
        views.admin_checkins_list,
        name="admin_checkins_list",
    ),
    path(
        "admin-panel/checkins/<int:assignment_id>/",
        views.admin_checkin_detail,
        name="admin_checkin_detail",
    ),
]
