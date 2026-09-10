from django import forms
from .models import JobPosition, Candidate, Interview

CSS = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'


class JobPositionForm(forms.ModelForm):
    class Meta:
        model = JobPosition
        fields = ['title', 'department', 'description', 'requirements', 'vacancies', 'status', 'deadline']
        widgets = {'deadline': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['first_name', 'last_name', 'email', 'phone', 'job_position', 'status', 'resume', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['interviewer', 'scheduled_at', 'location', 'notes', 'result']
        widgets = {'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS
