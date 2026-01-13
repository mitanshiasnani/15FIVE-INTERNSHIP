from django.contrib import admin
from .models import (
    Question,
    CheckInForm,
    CheckInFormQuestion,
    CheckInAssignment
)

admin.site.register(Question)
admin.site.register(CheckInForm)
admin.site.register(CheckInFormQuestion)
admin.site.register(CheckInAssignment)
