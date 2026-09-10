from django import forms
from .models import OTRequest

CSS = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'


class OTRequestForm(forms.ModelForm):
    class Meta:
        model = OTRequest
        fields = ['date', 'start_time', 'end_time', 'hours', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class OTReviewForm(forms.ModelForm):
    class Meta:
        model = OTRequest
        fields = ['status', 'review_comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [('approved', 'Approved'), ('rejected', 'Rejected')]
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS
