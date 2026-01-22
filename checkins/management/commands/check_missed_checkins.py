from django.core.management.base import BaseCommand
from django.utils import timezone

from checkins.models import CheckInForm, CheckInAssignment
from checkins.services.slack import send_admin_missed_checkin_dm


class Command(BaseCommand):
    help = "Notify admin about missed check-ins"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        checkins = CheckInForm.objects.filter(
            end_date__lt=today,
            admin_notified_on_complete=False,
        )

        for checkin in checkins:
            pending = checkin.assignments.filter(
                status="PENDING"
            )

            if pending.exists():
                send_admin_missed_checkin_dm(
                    checkin=checkin,
                    pending_assignments=pending,
                )

                # Prevent duplicate alerts
                checkin.admin_notified_on_complete = True
                checkin.save()
 