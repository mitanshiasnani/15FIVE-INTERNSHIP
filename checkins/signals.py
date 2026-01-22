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
@receiver(post_save, sender=CheckInForm)
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
@receiver(post_save, sender=CheckInAssignment)
def notify_employee_on_assignment(sender, instance, created, **kwargs):
    if not created:
        return  # only when assignment is first created

    employee = instance.employee
    profile = getattr(employee, "employee_profile", None)

    if profile and profile.slack_user_id:
        print("📢 SIGNAL FIRED →", employee.email)

        send_checkin_assigned_dm(
            slack_user_id=profile.slack_user_id,
            title=instance.checkin_form.title,
            start_date=instance.checkin_form.start_date,
            end_date=instance.checkin_form.end_date,
        )

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
@receiver(post_save, sender=CheckInForm)
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
@receiver(post_save, sender=CheckInAssignment)
def notify_employee_on_assignment(sender, instance, created, **kwargs):
    if not created:
        return  # only when assignment is first created

    employee = instance.employee
    profile = getattr(employee, "employee_profile", None)

    if profile and profile.slack_user_id:
        print("📢 SIGNAL FIRED →", employee.email)

        send_checkin_assigned_dm(
            slack_user_id=profile.slack_user_id,
            title=instance.checkin_form.title,
            start_date=instance.checkin_form.start_date,
            end_date=instance.checkin_form.end_date,
        )

