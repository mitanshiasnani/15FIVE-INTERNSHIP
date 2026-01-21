from slack_sdk import WebClient
from django.conf import settings

client = WebClient(token=settings.SLACK_BOT_TOKEN)

def send_checkin_assigned_dm(slack_user_id, checkin_title, deadline):
    if not slack_user_id:
        return

    message = (
        f"👋 Hey!\n\n"
        f"You’ve been assigned a new check-in:\n"
        f"*{checkin_title}*\n\n"
        f"🗓 Deadline: {deadline}\n\n"
        f"Please complete it on the 15Five portal 🚀"
    )

    client.chat_postMessage(
        channel=slack_user_id,
        text=message
    )
