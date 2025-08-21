from django import forms
from .models import HolidayRequest

class HolidayRequestForm(forms.ModelForm):
    class Meta:
        model = HolidayRequest
        fields = ['start_date', 'end_date']
