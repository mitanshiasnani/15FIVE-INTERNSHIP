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


class CheckInForm(models.Model):
    PERIOD_CHOICES = (
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    )

    title = models.CharField(max_length=255)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    deadline = models.DateTimeField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'ADMIN'}
    )
    is_active = models.BooleanField(default=True)
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
        ("PENDING", "Pending"),
        ("SUBMITTED", "Submitted"),
    )

    REVIEW_CHOICES = (
        ("PENDING", "Pending Review"),
        ("REVIEWED", "Reviewed"),
    )

    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    checkin_form = models.ForeignKey(CheckInForm, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    review_status = models.CharField(
        max_length=20,
        choices=REVIEW_CHOICES,
        default="PENDING"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.email} - {self.checkin_form.title}"


    
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
