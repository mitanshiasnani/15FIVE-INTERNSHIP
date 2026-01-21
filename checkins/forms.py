from django import forms
from .models import CheckInForm


class CheckInFormCreateForm(forms.ModelForm):
    class Meta:
        model = CheckInForm
        fields = ["title", "period", "start_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"})
        }
