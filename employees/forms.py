from django import forms
from .models import EmployeeProfile, EmergencyContact, Dependent


class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        exclude = ['created_at', 'updated_at']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'join_date': forms.DateInput(attrs={'type': 'date'}),
            'probation_end_date': forms.DateInput(attrs={'type': 'date'}),
            'registered_address': forms.Textarea(attrs={'rows': 2}),
            'current_address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # แสดง "ชื่อ (username)" แทน "ชื่อ (role)" ใน User Account dropdown
        # เพราะ Role คือสิทธิ์ใน system ≠ Job Title ในองค์กร
        from accounts.models import User as UserModel
        self.fields['user'].queryset = UserModel.objects.all()
        self.fields['user'].label_from_instance = lambda u: (
            f"{u.get_full_name() or u.username}  [{u.username}]"
        )
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput,
                                         forms.NumberInput, forms.Select)):
                field.widget.attrs.setdefault('class', 'form-input')
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault('class', 'form-input')
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.setdefault('class', 'form-input')
