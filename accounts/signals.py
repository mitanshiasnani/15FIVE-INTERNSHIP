from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, EmployeeProfile

@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    if created and instance.role == "EMPLOYEE":
        EmployeeProfile.objects.create(
            user=instance,
            full_name=instance.email.split("@")[0],
            designation="Not Assigned",
            department="Not Assigned"
        )
