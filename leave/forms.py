from django import forms
from .models import LeaveType, LeaveBalance, LeaveRequest

CSS = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'days', 'reason',
                  'medical_cert_name', 'medical_cert_sharepoint_url']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.sick_leave_id = kwargs.pop('sick_leave_id', None)
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            f.widget.attrs['class'] = CSS
        self.fields['medical_cert_name'].label = 'ชื่อไฟล์ใบรับรองแพทย์'
        self.fields['medical_cert_name'].required = False
        self.fields['medical_cert_sharepoint_url'].label = 'SharePoint URL (HR เท่านั้น)'
        self.fields['medical_cert_sharepoint_url'].required = False
        self.fields['medical_cert_sharepoint_url'].widget.attrs['placeholder'] = 'วาง SharePoint link ที่นี่'

    def clean(self):
        cleaned_data = super().clean()
        leave_type = cleaned_data.get('leave_type')
        days = cleaned_data.get('days')
        cert_name = cleaned_data.get('medical_cert_name', '').strip()

        is_sick = False
        if leave_type:
            name_lower = leave_type.name.lower()
            name_th = (leave_type.name_th or '').lower()
            is_sick = 'sick' in name_lower or 'ป่วย' in name_th or 'ป่วย' in name_lower

        if is_sick and days and days > 3:
            if not cert_name:
                self.add_error(
                    'medical_cert_name',
                    'ลาป่วยเกิน 3 วัน ต้องระบุชื่อไฟล์ใบรับรองแพทย์'
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
