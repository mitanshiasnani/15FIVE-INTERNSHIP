from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, EmployeeProfile


@receiver(
    post_save,
    sender=User,
    dispatch_uid="employee_profile_autocreate"
)
def create_employee_profile(sender, instance, **kwargs):
    if instance.role == "EMPLOYEE":
        EmployeeProfile.objects.get_or_create(user=instance)
