from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, EmployeeProfile

@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'EMPLOYEE':
        EmployeeProfile.objects.get_or_create(
            user=instance
        )

