# checkins/services/slack.py

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

if not SLACK_BOT_TOKEN:
    raise RuntimeError("❌ SLACK_BOT_TOKEN not set")

client = WebClient(token=SLACK_BOT_TOKEN)

print("🔥 SLACK SERVICE LOADED")


# -------------------------------------------------
# EMPLOYEE: Check-in assigned DM
# -------------------------------------------------
def send_checkin_assigned_dm(slack_user_id, title, start_date, end_date):
    try:
        print(f"📩 Slack DM attempt → {slack_user_id}")

        response = client.chat_postMessage(
            channel=slack_user_id,
            text=(
                f"📝 *New Check-In Assigned*\n\n"
                f"*{title}*\n"
                f"📅 {start_date} → {end_date}\n\n"
                f"Please complete it before the deadline."
            )
        )

        print("✅ Slack DM SENT:", response["ts"])

    except SlackApiError as e:
        print("❌ Slack DM FAILED:", e.response["error"])


# -------------------------------------------------
# ADMIN: All employees submitted
# -------------------------------------------------
def send_admin_all_submitted_dm(slack_user_id, title, start_date, end_date):
    try:
        print(f"📩 Admin Slack DM → {slack_user_id}")

        response = client.chat_postMessage(
            channel=slack_user_id,
            text=(
                f"✅ *All Check-Ins Submitted*\n\n"
                f"*{title}*\n"
                f"📅 {start_date} → {end_date}\n\n"
                f"All employees have submitted their check-in."
            )
        )

        print("✅ Admin Slack DM SENT:", response["ts"])

    except SlackApiError as e:
        print("❌ Admin Slack DM FAILED:", e.response["error"])


def send_admin_all_submitted_dm(*, title, start_date, end_date):
    from django.conf import settings

    admin_slack_user_id = settings.ADMIN_SLACK_USER_ID  # you will add this

    if not admin_slack_user_id:
        print("⚠️ ADMIN_SLACK_USER_ID not set")
        return

    message = (
        "✅ *All Check-Ins Submitted*\n\n"
        f"*{title}*\n"
        f"📅 {start_date} → {end_date}\n\n"
        "All employees have submitted their responses."
    )

    client.chat_postMessage(
        channel=admin_slack_user_id,
        text=message
    )

    print("📢 ADMIN SLACK DM SENT")

