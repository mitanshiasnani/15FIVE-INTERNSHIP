from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, EmployeeProfile


@receiver(post_save, sender=User)
def ensure_employee_profile(sender, instance, **kwargs):
    """
    Ensure every EMPLOYEE always has an EmployeeProfile.
    REQUIRED for Slack DM delivery.
    """
    if instance.role == "EMPLOYEE":
        EmployeeProfile.objects.get_or_create(user=instance)
