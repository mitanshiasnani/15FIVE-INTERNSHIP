from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CheckInForm, CheckInFormQuestion, Question


@receiver(post_save, sender=CheckInForm)
def attach_default_questions(sender, instance, created, **kwargs):
    if not created:
        return

    default_questions = Question.objects.filter(is_default=True)

    bulk_links = []
    for question in default_questions:
        bulk_links.append(
            CheckInFormQuestion(
                checkin_form=instance,
                question=question
            )
        )

    CheckInFormQuestion.objects.bulk_create(
        bulk_links,
        ignore_conflicts=True
    )
