from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count

from django.utils import timezone
from .models import User
from .forms import LoginForm, UserCreateForm, UserEditForm
from recruitment.models import JobPosition, Candidate
from training.models import TrainingProgram, TrainingEnrollment
from appraisals.models import AppraisalCycle, Appraisal
from leave.models import LeaveRequest
from overtime.models import OTRequest
from attendance.models import AttendanceRecord


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('dashboard')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    today = timezone.localdate()
    context = {
        'total_employees': User.objects.filter(role='employee').count(),
        'open_jobs': JobPosition.objects.filter(status='open').count(),
        'active_trainings': TrainingProgram.objects.filter(status__in=['upcoming', 'ongoing']).count(),
        'pending_appraisals': Appraisal.objects.filter(status__in=['pending', 'self_review', 'manager_review']).count(),
        'recent_candidates': Candidate.objects.select_related('job_position').order_by('-applied_at')[:5],
        'upcoming_trainings': TrainingProgram.objects.filter(status='upcoming').order_by('start_date')[:5],
        'pending_leave': LeaveRequest.objects.filter(status='pending').count(),
        'pending_ot': OTRequest.objects.filter(status='pending').count(),
        'today_attendance': AttendanceRecord.objects.filter(date=today).count(),
    }
    return render(request, 'dashboard.html', context)


@login_required
def user_list(request):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    users = User.objects.all().order_by('role', 'first_name')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def user_create(request):
    if not request.user.is_super_admin:
        messages.error(request, 'Only Super Admin can create users.')
        return redirect('user_list')
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'User created successfully.')
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create User'})


@login_required
def user_edit(request, pk):
    if not request.user.is_super_admin:
        messages.error(request, 'Only Super Admin can edit users.')
        return redirect('user_list')
    user = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'User updated successfully.')
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Edit User', 'object': user})


@login_required
def user_delete(request, pk):
    if not request.user.is_super_admin:
        messages.error(request, 'Only Super Admin can delete users.')
        return redirect('user_list')
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted.')
        return redirect('user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'object': user})
