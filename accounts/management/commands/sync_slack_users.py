from django.core.management.base import BaseCommand
from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from accounts.models import EmployeeProfile


class Command(BaseCommand):
    help = "Sync Slack user IDs with EmployeeProfile using email matching"

    def handle(self, *args, **kwargs):
        client = WebClient(token=settings.SLACK_BOT_TOKEN)

        try:
            slack_users = []
            cursor = None

            while True:
                response = client.users_list(cursor=cursor, limit=200)
                slack_users.extend(response["members"])
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

            updated = 0
            skipped = 0

            for user in slack_users:
                if user.get("deleted"):
                    continue

                profile = user.get("profile", {})
                email = profile.get("email")
                slack_id = user.get("id")

                if not email:
                    continue

                try:
                    emp_profile = EmployeeProfile.objects.get(user__email=email)

                    if emp_profile.slack_user_id != slack_id:
                        emp_profile.slack_user_id = slack_id
                        emp_profile.save()
                        updated += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"Linked {email} → {slack_id}")
                        )
                    else:
                        skipped += 1

                except EmployeeProfile.DoesNotExist:
                    continue

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Sync complete: {updated} updated, {skipped} already linked"
                )
            )

        except SlackApiError as e:
            self.stderr.write(
                self.style.ERROR(f"❌ Slack API error: {e.response['error']}")
            )
