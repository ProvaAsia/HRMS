from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils.crypto import get_random_string
from collections import defaultdict
import calendar

from django.utils import timezone
from .models import User
from .forms import LoginForm, UserCreateForm, UserEditForm, InviteUserForm, SetPasswordForm
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
        'active_trainings': TrainingProgram.objects.filter(status__in=['upcoming', 'ongoing']).count(),
        'pending_appraisals': Appraisal.objects.filter(status__in=['pending', 'self_review', 'manager_review']).count(),
        'upcoming_trainings': TrainingProgram.objects.filter(status='upcoming').order_by('start_date')[:5],
        'pending_leave': LeaveRequest.objects.filter(status='pending').count(),
        'pending_ot': OTRequest.objects.filter(status='pending').count(),
        'today_attendance': AttendanceRecord.objects.filter(date=today).count(),
    }

    # Manager-specific: pending approvals from direct reports + monthly leave calendar
    user = request.user
    if user.can_approve:
        direct_reports = user.get_direct_report_users()
        if direct_reports.exists():
            # Pending leave/OT from direct reports
            context['mgr_pending_leave'] = LeaveRequest.objects.filter(
                employee__in=direct_reports, status='pending'
            ).select_related('employee', 'leave_type').order_by('-created_at')[:10]
            context['mgr_pending_ot'] = OTRequest.objects.filter(
                employee__in=direct_reports, status='pending'
            ).select_related('employee').order_by('-created_at')[:10]
            context['mgr_pending_leave_count'] = LeaveRequest.objects.filter(
                employee__in=direct_reports, status='pending'
            ).count()
            context['mgr_pending_ot_count'] = OTRequest.objects.filter(
                employee__in=direct_reports, status='pending'
            ).count()

            # Monthly leave calendar — approved leaves this month
            month_start = today.replace(day=1)
            month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
            approved_leaves = LeaveRequest.objects.filter(
                employee__in=direct_reports,
                status='approved',
                start_date__lte=month_end,
                end_date__gte=month_start,
            ).select_related('employee', 'leave_type').order_by('start_date')

            # Build calendar days list
            num_days = month_end.day
            from datetime import date as date_cls
            days_data = []
            for day in range(1, num_days + 1):
                d = date_cls(today.year, today.month, day)
                on_leave = []
                for lr in approved_leaves:
                    if lr.start_date <= d <= lr.end_date:
                        on_leave.append(lr)
                days_data.append({
                    'date': d,
                    'weekday': d.weekday(),  # 0=Mon,6=Sun
                    'is_today': d == today,
                    'on_leave': on_leave,
                    'on_leave_extra': max(0, len(on_leave) - 2),
                })
            # Pad the start of the grid (Monday = 0)
            first_offset = month_start.weekday()
            empty_prefix = list(range(first_offset))
            context['calendar_days'] = days_data
            context['calendar_empty_prefix'] = empty_prefix
            context['calendar_month'] = today

            # Team attendance today — grouped by department
            PRESENT_STATUSES = {'present', 'late', 'wfh', 'half_day'}
            today_records = AttendanceRecord.objects.filter(
                employee__in=direct_reports, date=today
            ).select_related('employee')
            records_by_emp = {r.employee_id: r for r in today_records}

            # ดึง approved leave ที่ครอบคลุมวันนี้ — ถ้าไม่มี AttendanceRecord ก็นับเป็น on_leave
            approved_today = LeaveRequest.objects.filter(
                employee__in=direct_reports,
                status='approved',
                start_date__lte=today,
                end_date__gte=today,
            ).values_list('employee_id', 'leave_type__name')
            on_leave_emps = {emp_id: lt_name for emp_id, lt_name in approved_today}

            dept_data = defaultdict(lambda: {
                'total': 0, 'present': 0, 'on_leave': 0, 'absent': 0, 'members': []
            })

            for emp in direct_reports.order_by('department', 'first_name'):
                dept = emp.department.strip() if emp.department else 'ไม่ระบุแผนก'
                record = records_by_emp.get(emp.pk)
                dept_data[dept]['total'] += 1

                if record:
                    if record.status in PRESENT_STATUSES:
                        member_status = 'present'
                        dept_data[dept]['present'] += 1
                    elif record.status == 'leave':
                        member_status = 'leave'
                        dept_data[dept]['on_leave'] += 1
                    else:
                        member_status = 'absent'
                        dept_data[dept]['absent'] += 1
                elif emp.pk in on_leave_emps:
                    # ไม่มี attendance record แต่มี approved leave → on leave
                    member_status = 'leave'
                    dept_data[dept]['on_leave'] += 1
                else:
                    member_status = 'no_record'
                    dept_data[dept]['absent'] += 1

                dept_data[dept]['members'].append({
                    'emp': emp,
                    'status': member_status,
                    'record': record,
                    'leave_type_name': on_leave_emps.get(emp.pk),
                })

            dept_dict = dict(dept_data)
            total_present = sum(d['present'] for d in dept_dict.values())
            total_leave = sum(d['on_leave'] for d in dept_dict.values())
            total_absent = sum(d['absent'] for d in dept_dict.values())
            context['team_attendance_depts'] = dept_dict
            context['team_attendance_summary'] = {
                'total': direct_reports.count(),
                'present': total_present,
                'on_leave': total_leave,
                'absent': total_absent,
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


@login_required
def invite_user(request):
    """HR/Admin creates an inactive user and gets a setup link to share."""
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')

    form = InviteUserForm(request.POST or None)
    setup_link = None

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        role = form.cleaned_data['role']
        first_name = form.cleaned_data.get('first_name', '')
        last_name = form.cleaned_data.get('last_name', '')

        # Generate a unique token used as username placeholder
        token = get_random_string(32)
        username = email.split('@')[0] + '_' + get_random_string(6)

        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=False,
        )
        # Store token in password field (hashed); real activation will set real password
        user.set_unusable_password()
        # We'll store the token via a dedicated profile field; use last_name as temp storage
        # Instead, store token in the user's password field temporarily as a marker
        # Use a simple approach: store token in a way retrievable by the activate view
        # We save token as part of username for lookup
        user.username = f'invite_{token}'
        user.save()

        setup_link = request.build_absolute_uri(
            f'/accounts/activate/{token}/'
        )
        messages.success(
            request,
            f'Invitation created for {email}. Copy the setup link below and send it to the user.'
        )

    return render(request, 'accounts/invite_user.html', {
        'form': form,
        'setup_link': setup_link,
    })


def activate_account(request, token):
    """New user sets their username and password via the invite link."""
    user = get_object_or_404(User, username=f'invite_{token}', is_active=False)

    form = SetPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']

        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            form.add_error('username', 'This username is already taken.')
        else:
            user.username = username
            user.set_password(password)
            user.is_active = True
            user.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or username}! Your account is active.')
            return redirect('dashboard')

    return render(request, 'accounts/activate_account.html', {
        'form': form,
        'invited_email': user.email,
    })
