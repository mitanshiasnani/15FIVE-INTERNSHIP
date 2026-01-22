from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    CheckInForm,
    CheckInFormQuestion,
    Question,
    CheckInAssignment,
)

from checkins.services.slack import send_checkin_assigned_dm


# -------------------------------------------------
# Attach default questions when CheckInForm created
# -------------------------------------------------
@receiver(
    post_save,
    sender=CheckInForm,
    dispatch_uid="checkin_attach_default_questions_v1"
)
def attach_default_questions(sender, instance, created, **kwargs):
    if not created:
        return

    default_questions = Question.objects.filter(is_default=True)

    CheckInFormQuestion.objects.bulk_create(
        [
            CheckInFormQuestion(
                checkin_form=instance,
                question=question
            )
            for question in default_questions
        ],
        ignore_conflicts=True
    )


# -------------------------------------------------
# 🔔 Notify employee when assigned a check-in (Slack)
# -------------------------------------------------
@receiver(
    post_save,
    sender=CheckInAssignment,
    dispatch_uid="checkin_assignment_slack_dm_v1"
)
def notify_employee_on_assignment(sender, instance, created, **kwargs):
    """
    Sends EXACTLY ONE Slack DM per assignment.
    """
    if not created:
        return  # 🚫 prevents duplicates on updates

    employee = instance.employee
    profile = getattr(employee, "employee_profile", None)

    if not profile or not profile.slack_user_id:
        return

    print("📢 SLACK SIGNAL →", employee.email)

    send_checkin_assigned_dm(
        slack_user_id=profile.slack_user_id,
        title=instance.checkin_form.title,
        start_date=instance.checkin_form.start_date,
        end_date=instance.checkin_form.end_date,
    )

from django.db.models import Q
from checkins.services.slack import send_admin_all_submitted_dm


@receiver(
    post_save,
    sender=CheckInAssignment,
    dispatch_uid="checkin_admin_notify_all_submitted_v1"
)
def notify_admin_when_all_submitted(sender, instance, **kwargs):
    checkin = instance.checkin_form

    # If admin already notified → STOP
    if checkin.admin_notified_on_complete:
        return

    # Count assignments
    total = checkin.assignments.count()
    submitted = checkin.assignments.filter(status="SUBMITTED").count()

    if total > 0 and total == submitted:
        print("🎯 ALL EMPLOYEES SUBMITTED → ADMIN NOTIFY")

        send_admin_all_submitted_dm(
            title=checkin.title,
            start_date=checkin.start_date,
            end_date=checkin.end_date,
        )

        # Mark as notified (VERY IMPORTANT)
        checkin.admin_notified_on_complete = True
        checkin.save(update_fields=["admin_notified_on_complete"])
