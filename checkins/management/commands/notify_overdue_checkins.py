from django.core.management.base import BaseCommand
from django.utils import timezone

from checkins.models import CheckInForm, CheckInAssignment
from checkins.services.slack import send_admin_all_submitted_dm


class Command(BaseCommand):
    help = "Notify admin when check-in deadline passes and submissions are pending"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        # Only check-ins whose deadline has passed
        checkins = CheckInForm.objects.filter(
            end_date__lt=today,
            admin_notified_on_complete=False,  # reuse flag ONLY for overdue case
        )

        for checkin in checkins:
            assignments = CheckInAssignment.objects.filter(
                checkin_form=checkin
            )

            total = assignments.count()
            submitted = assignments.filter(status="SUBMITTED").count()

            if total == 0:
                continue

            # ❗ Deadline passed AND some employees pending
            if submitted < total:
                pending = total - submitted

                print(
                    f"⏰ OVERDUE → CheckIn {checkin.id} | "
                    f"submitted={submitted}, pending={pending}"
                )

                send_admin_all_submitted_dm(
                    title=f"{checkin.title} (Deadline Passed)",
                    start_date=checkin.start_date,
                    end_date=checkin.end_date,
                )

                # Lock to avoid duplicate admin DMs
                checkin.admin_notified_on_complete = True
                checkin.save(update_fields=["admin_notified_on_complete"])

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Admin notified for overdue check-in {checkin.id}"
                    )
                )
