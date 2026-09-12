from django import forms
from .models import LeaveType, LeaveBalance, LeaveRequest

CSS = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'days', 'reason', 'medical_certificate']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.sick_leave_id = kwargs.pop('sick_leave_id', None)
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            if name == 'medical_certificate':
                f.widget.attrs['class'] = (
                    'w-full text-sm text-gray-700 file:mr-3 file:py-1.5 file:px-3 '
                    'file:rounded-lg file:border-0 file:text-xs file:font-medium '
                    'file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 '
                    'border border-gray-300 rounded-lg px-2 py-1.5'
                )
                f.required = False
            else:
                f.widget.attrs['class'] = CSS

    def clean(self):
        cleaned_data = super().clean()
        leave_type = cleaned_data.get('leave_type')
        days = cleaned_data.get('days')
        cert = cleaned_data.get('medical_certificate')

        # Check if this is a sick leave type (by name contains ป่วย or Sick)
        is_sick = False
        if leave_type:
            name_lower = leave_type.name.lower()
            name_th = (leave_type.name_th or '').lower()
            is_sick = 'sick' in name_lower or 'ป่วย' in name_th or 'ป่วย' in name_lower

        if is_sick and days and days > 3:
            if not cert and not self.files.get('medical_certificate'):
                self.add_error(
                    'medical_certificate',
                    'ลาป่วยเกิน 3 วัน ต้องแนบใบรับรองแพทย์'
                )
        return cleaned_data


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
