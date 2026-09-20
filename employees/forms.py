from django import forms
from .models import EmployeeProfile, EmployeeDocument, EmergencyContact, Dependent
from accounts.models import User as UserModel


class EmployeeProfileForm(forms.ModelForm):

    # Field พิเศษ — ดึงจาก User.role (ไม่ใช่ field ใน EmployeeProfile)
    role = forms.ChoiceField(
        choices=UserModel.ROLE_CHOICES,
        label='Role',
        required=True,
    )

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

        # แสดง "ชื่อ [username]" ใน User Account dropdown
        self.fields['user'].queryset = UserModel.objects.all()
        self.fields['user'].label_from_instance = lambda u: (
            f"{u.get_full_name() or u.username}  [{u.username}]"
        )

        # Pre-fill role จาก user ที่ link อยู่ (กรณี edit)
        if self.instance and self.instance.pk:
            try:
                self.fields['role'].initial = self.instance.user.role
            except Exception:
                pass

        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput,
                                         forms.NumberInput, forms.Select)):
                field.widget.attrs.setdefault('class', 'form-input')
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault('class', 'form-input')
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.setdefault('class', 'form-input')

    def save(self, commit=True):
        profile = super().save(commit=commit)
        # บันทึก role ลง User model ด้วย
        new_role = self.cleaned_data.get('role')
        if new_role and profile.user:
            profile.user.role = new_role
            profile.user.save(update_fields=['role'])
        return profile


class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = ['doc_type', 'doc_name', 'doc_number', 'issue_date', 'expiry_date', 'status', 'file', 'note']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput,
                                         forms.NumberInput, forms.Select)):
                field.widget.attrs.setdefault('class', 'form-input')
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault('class', 'form-input')
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.setdefault('class', 'form-input')
