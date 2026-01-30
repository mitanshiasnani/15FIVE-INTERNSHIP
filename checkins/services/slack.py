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
# EMPLOYEE: Check-in assigned DM (UNCHANGED)
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
# ADMIN: All employees submitted (UNCHANGED)
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


# -------------------------------------------------
# EMPLOYEE: Admin reviewed check-in (NEW, SAFE)
# -------------------------------------------------
# def send_admin_reviewed_dm(slack_user_id, period, admin_comment):
#     try:
#         response = client.chat_postMessage(
#             channel=slack_user_id,
#             text=(
#                 f"✅ *Your Check-In Has Been Reviewed*\n\n"
#                 f"*Period:* {period}\n\n"
#                 f"*Admin Comment:*\n"
#                 f"{admin_comment or 'No comment provided.'}"
#             )
#         )

#         print("✅ Review Slack DM SENT:", response["ts"])

#     except SlackApiError as e:
#         print("❌ Review Slack DM FAILED:", e.response["error"])

def send_admin_reviewed_dm(slack_user_id, title, start_date, end_date, comment):
    try:
        client.chat_postMessage(
            channel=slack_user_id,
            text=(
                "🟢 *Check-In Reviewed*\n\n"
                f"*{title}*\n"
                f"📅 {start_date} → {end_date}\n\n"
                f"*Admin Comment:*\n{comment or 'No comment provided.'}"
            )
        )
        print("✅ Review DM sent to employee")

    except SlackApiError as e:
        print("❌ Review DM failed:", e.response["error"])
