from django.urls import path
from .views import admin_dashboard, employee_dashboard, admin_profile, add_employee, employee_list, employee_dashboard,employee_checkins,employee_history,employee_settings,employee_profile    

urlpatterns = [
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-profile/', admin_profile, name='admin_profile'),
    path('add-employee/', add_employee, name='add_employee'),
    path("employee/dashboard/", employee_dashboard, name="employee_dashboard"),
    path('employees/', employee_list, name='employee_list'),
    path("employee/checkins/", employee_checkins, name="employee_checkins"),
    path("employee/history/", employee_history, name="employee_history"),
    path("employee/settings/", employee_settings, name="employee_settings"),
    path("employee/profile/", employee_profile, name="employee_profile"),
]
