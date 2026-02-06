from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta

from checkins.models import CheckInAssignment
from checkins.services.slack import send_checkin_deadline_reminder_dm


class Command(BaseCommand):
    help = "Send Slack reminders for check-ins nearing deadline"

    def handle(self, *args, **options):
        today = now().date()
        reminder_date = today + timedelta(days=1)  # 24 hours before deadline

        assignments = CheckInAssignment.objects.filter(
            status__in=["PENDING", "PARTIAL"],
            checkin_form__end_date=reminder_date,
            reminder_sent=False
        ).select_related("employee", "checkin_form")

        self.stdout.write(f"🔍 Found {assignments.count()} pending reminders")

        for assignment in assignments:
            employee = assignment.employee
            profile = getattr(employee, "employee_profile", None)

            if not profile or not profile.slack_user_id:
                continue

            send_checkin_deadline_reminder_dm(
                slack_user_id=profile.slack_user_id,
                title=assignment.checkin_form.title,
                end_date=assignment.checkin_form.end_date
            )

            assignment.reminder_sent = True
            assignment.save(update_fields=["reminder_sent"])

        self.stdout.write("✅ Reminder job completed")
