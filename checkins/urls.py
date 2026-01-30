from django.urls import path
from . import views
from .views import manage_default_questions

urlpatterns = [

    # ================= CREATE =================
    path(
        "create/",
        views.create_checkin,
        name="create_checkin"
    ),

    # ================= ADMIN =================

    # List all check-ins
    path(
        "admin-panel/checkins/",
        views.admin_checkins_list,
        name="admin_checkins_list"
    ),

    # Check-in overview → list employees + status
    path(
        "admin-panel/checkins/<int:checkin_id>/",
        views.admin_checkin_overview,
        name="admin_checkin_overview"
    ),

    # Assignment review → answers + mark reviewed
    path(
        "admin-panel/checkins/assignment/<int:assignment_id>/",
        views.admin_assignment_review,
        name="admin_assignment_review"
    ),
    

    path(
        "admin/default-questions/",
        manage_default_questions,
        name="manage_default_questions"
    ),


]
