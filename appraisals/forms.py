from django import forms
from .models import AppraisalCycle, Appraisal, Goal

CSS = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'


class AppraisalCycleForm(forms.ModelForm):
    class Meta:
        model = AppraisalCycle
        fields = ['name', 'description', 'start_date', 'end_date', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class AppraisalForm(forms.ModelForm):
    class Meta:
        model = Appraisal
        fields = ['employee', 'manager', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        self.fields['employee'].queryset = User.objects.filter(is_active=True)
        self.fields['manager'].queryset = User.objects.filter(role__in=['hr_manager', 'super_admin'])
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class SelfReviewForm(forms.ModelForm):
    class Meta:
        model = Appraisal
        fields = ['self_rating', 'self_comments']
        widgets = {'self_rating': forms.Select(choices=[(i, f'{i} Star{"s" if i>1 else ""}') for i in range(1, 6)])}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class ManagerReviewForm(forms.ModelForm):
    class Meta:
        model = Appraisal
        fields = ['manager_rating', 'manager_comments', 'status']
        widgets = {'manager_rating': forms.Select(choices=[(i, f'{i} Star{"s" if i>1 else ""}') for i in range(1, 6)])}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'description', 'target_date', 'status', 'weight', 'achievement']
        widgets = {'target_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = CSS
