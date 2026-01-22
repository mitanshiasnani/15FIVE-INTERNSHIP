from django.db import models
from accounts.models import User


class Question(models.Model):
    question_text = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'ADMIN'}
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text[:50]



from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils.dateparse import parse_date

from django.db import models
from django.conf import settings
from datetime import timedelta

class CheckInForm(models.Model):
    PERIOD_CHOICES = [
        ("WEEKLY", "Weekly"),
        ("MONTHLY", "Monthly"),
    ]

    title = models.CharField(max_length=255)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    admin_notified_on_complete = models.BooleanField(default=False)

    start_date = models.DateField()
    end_date = models.DateField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_checkins"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title





class CheckInFormQuestion(models.Model):
    checkin_form = models.ForeignKey(CheckInForm, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('checkin_form', 'question')


class CheckInAssignment(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),          # Not started
        ("PARTIAL", "Partially Filled"), # Draft saved
        ("SUBMITTED", "Submitted"),
    )

    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    checkin_form = models.ForeignKey(CheckInForm, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    review_status = models.CharField(
        max_length=20,
        choices=(
            ("PENDING", "Pending Review"),
            ("REVIEWED", "Reviewed"),
        ),
        default="PENDING"
    )

    assigned_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)





    
class CheckInAnswer(models.Model):
    assignment = models.ForeignKey(
        CheckInAssignment,
        on_delete=models.CASCADE,
        related_name="answers"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'EMPLOYEE'}
    )
    answer_text = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('assignment', 'question')

    def __str__(self):
        return f"{self.employee.email} - {self.question.question_text[:30]}"
