from django import forms
from .models import TrainingProgram, TrainingEnrollment

CSS = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'


class TrainingProgramForm(forms.ModelForm):
    class Meta:
        model = TrainingProgram
        fields = ['title', 'category', 'description', 'trainer', 'start_date', 'end_date', 'location', 'max_participants', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = TrainingEnrollment
        fields = ['employee', 'status', 'completion_date', 'score', 'notes']
        widgets = {'completion_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        self.fields['employee'].queryset = User.objects.filter(is_active=True)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class BulkEnrollForm(forms.Form):
    """Enroll multiple participants at once — by department or by individual selection."""
    from employees.models import Department

    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='— Select department (optional) —',
        label='Enroll entire department',
    )
    employees = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        label='Or select individual employees',
        widget=forms.SelectMultiple(attrs={'size': '8'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        from employees.models import Department
        self.fields['department'].queryset = Department.objects.all()
        self.fields['employees'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS
