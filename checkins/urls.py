from django.urls import path
from . import views

urlpatterns = [
    # Admin creates check-in
    path(
        "checkins/create/",
        views.create_checkin,
        name="create_checkin"
    ),

    # Employee
    path(
        "employee/checkins/",
        views.employee_checkins,
        name="employee_checkins"
    ),
    path(
        "employee/checkins/<int:assignment_id>/",
        views.employee_checkin_form,
        name="employee_checkin_form"
    ),

    # Admin – history (grouped by form)
    path(
        "admin-panel/checkins/",
        views.admin_checkins_list,
        name="admin_checkins_list"
    ),

    # ✅ Admin – form-level detail (THIS IS THE ONLY VIEW LINK)
    path(
        "admin-panel/checkins/form/<int:form_id>/",
        views.admin_checkin_form_detail,
        name="admin_checkin_form_detail"
    ),
    path(
    "dashboard/employees/<int:employee_id>/checkins/",
    views.admin_employee_checkins,
    name="admin_employee_checkins"
),
path(
    "admin-panel/checkins/assignment/<int:assignment_id>/",
    views.admin_checkin_detail,
    name="admin_checkin_detail"
),


]
