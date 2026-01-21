from slack_sdk import WebClient
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

client = WebClient(token=settings.SLACK_BOT_TOKEN)


def send_checkin_assigned_dm(slack_user_id, title, deadline):
    try:
        # 1️⃣ Open DM channel
        response = client.conversations_open(users=[slack_user_id])
        channel_id = response["channel"]["id"]

        # 2️⃣ Send message
        client.chat_postMessage(
            channel=channel_id,
            text=(
                f"📋 *New Check-in Assigned*\n\n"
                f"*{title}*\n"
                f"🕒 Deadline: *{deadline}*\n\n"
                f"Please submit it on the 15Five portal ✅"
            )
        )

    except Exception as e:
        logger.error(f"Slack DM failed for {slack_user_id}: {e}")
