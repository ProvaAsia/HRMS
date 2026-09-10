from django import forms
from .models import LeaveType, LeaveBalance, LeaveRequest

CSS = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'days', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class ReviewForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['status', 'review_comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [('approved', 'Approved'), ('rejected', 'Rejected')]
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = ['name', 'days_per_year', 'is_paid', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class LeaveBalanceForm(forms.ModelForm):
    class Meta:
        model = LeaveBalance
        fields = ['employee', 'leave_type', 'year', 'entitled_days']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        self.fields['employee'].queryset = User.objects.filter(is_active=True)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS
