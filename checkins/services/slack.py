from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

client = WebClient(token=settings.SLACK_BOT_TOKEN)


# --------------------------------------------------
# INTERNAL HELPER
# --------------------------------------------------
def _send_dm(slack_user_id, text):
    if not slack_user_id:
        logger.warning("Slack user ID missing — DM not sent")
        return

    try:
        response = client.conversations_open(users=[slack_user_id])
        channel_id = response["channel"]["id"]

        client.chat_postMessage(
            channel=channel_id,
            text=text
        )

    except SlackApiError as e:
        logger.error(f"Slack DM failed: {e.response['error']}")


# --------------------------------------------------
# EMPLOYEE: CHECK-IN ASSIGNED
# --------------------------------------------------
def send_checkin_assigned_dm(slack_user_id, title, start_date, end_date):
    message = (
        f"📝 *New Check-In Assigned*\n\n"
        f"*Title:* {title}\n"
        f"*Period:* {start_date} → {end_date}\n\n"
        f"Please complete it on the portal."
    )

    _send_dm(slack_user_id, message)


# --------------------------------------------------
# ADMIN: ALL EMPLOYEES SUBMITTED
# --------------------------------------------------
def send_admin_all_submitted_dm(slack_user_id, title, start_date, end_date):
    message = (
        f"✅ *All Check-Ins Submitted*\n\n"
        f"*Title:* {title}\n"
        f"*Period:* {start_date} → {end_date}\n\n"
        f"All employees have completed their check-in."
    )

    _send_dm(slack_user_id, message)


# --------------------------------------------------
# EMPLOYEE: CHECK-IN REVIEWED
# --------------------------------------------------
def send_checkin_reviewed_dm(slack_user_id, title):
    message = (
        f"✅ *Check-In Reviewed*\n\n"
        f"Your check-in *{title}* has been reviewed by the admin.\n\n"
        f"Thank you for submitting on time 🙌"
    )

    _send_dm(slack_user_id, message)
