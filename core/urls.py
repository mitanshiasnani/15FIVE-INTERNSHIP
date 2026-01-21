from django.urls import path
from .views import (
    admin_dashboard,
    admin_profile,
    add_employee,
    employee_list,
    employee_dashboard,
    employee_checkins,
    employee_checkin_form,
    employee_history,
    employee_settings,
    employee_profile,
    admin_settings,
)

urlpatterns = [
    # ================= ADMIN =================
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-profile/', admin_profile, name='admin_profile'),
    path('add-employee/', add_employee, name='add_employee'),
    path('employees/', employee_list, name='employee_list'),

    # ================= EMPLOYEE =================
    path('employee/dashboard/', employee_dashboard, name='employee_dashboard'),
    path('employee/checkins/', employee_checkins, name='employee_checkins'),
    path('employee/checkins/<int:assignment_id>/', employee_checkin_form, name='employee_checkin_form'),
    path('employee/history/', employee_history, name='employee_history'),
    path('employee/settings/', employee_settings, name='employee_settings'),
    path('employee/profile/', employee_profile, name='employee_profile'),
    path("admin/settings/", admin_settings, name="admin_seetings"),

]
