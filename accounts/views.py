from django.shortcuts import render, redirect, get_object_or_404
from hrms.ratelimit import is_rate_limited
from django.http import HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils.crypto import get_random_string
from collections import defaultdict
import calendar

from django.utils import timezone
from .models import User, LoginAttempt
from .forms import LoginForm, UserCreateForm, UserEditForm, InviteUserForm, SetPasswordForm
from training.models import TrainingProgram, TrainingEnrollment
from appraisals.models import AppraisalCycle, Appraisal
from leave.models import LeaveRequest
from overtime.models import OTRequest
from attendance.models import AttendanceRecord


def _get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if is_rate_limited(request, key='ip', rate='10/m', method='POST'):
        return render(request, 'accounts/rate_limited.html', {'wait': 60}, status=429)

    form = LoginForm(request, data=request.POST or None)
    error_msg = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        # ── Check lockout BEFORE validating credentials ──
        if LoginAttempt.is_account_locked(username):
            return render(request, 'accounts/account_locked.html', {'locked_username': username})

        if form.is_valid():
            user = form.get_user()
            # Record successful login
            LoginAttempt.objects.create(
                username=username,
                ip_address=_get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
                success=True,
            )
            login(request, user)
            return redirect('dashboard')
        else:
            # Record failed attempt
            LoginAttempt.objects.create(
                username=username,
                ip_address=_get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
                success=False,
            )
            failures = LoginAttempt.consecutive_failures(username)
            remaining = max(0, LoginAttempt.MAX_FAILURES - failures)
            if LoginAttempt.is_account_locked(username):
                return render(request, 'accounts/account_locked.html', {'locked_username': username})
            if remaining <= 2:
                error_msg = f'รหัสผ่านผิด — เหลืออีก {remaining} ครั้ง บัญชีจะถูกล็อค'

    return render(request, 'accounts/login.html', {'form': form, 'lockout_warning': error_msg})


# ── Admin: locked accounts management ──────────────────────────────────────

@login_required
def locked_users_view(request):
    """Show all accounts that are currently locked."""
    if not request.user.is_admin:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')

    # Find usernames with 5+ consecutive failures
    all_usernames = (
        LoginAttempt.objects.values_list('username', flat=True).distinct()
    )
    locked = [u for u in all_usernames if LoginAttempt.is_account_locked(u)]

    # Enrich with User objects where available
    user_objs = {u.username: u for u in User.objects.filter(username__in=locked)}
    locked_list = [
        {
            'username': uname,
            'user': user_objs.get(uname),
            'failures': LoginAttempt.consecutive_failures(uname),
        }
        for uname in locked
    ]
    return render(request, 'accounts/locked_users.html', {'locked_list': locked_list})


@login_required
def unlock_user_view(request, username):
    """Admin clears failed login attempts to unlock the account."""
    if not request.user.is_admin:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    if request.method == 'POST':
        LoginAttempt.objects.filter(username=username, success=False).delete()
        messages.success(request, f'ปลดล็อคบัญชี "{username}" เรียบร้อยแล้ว')
    return redirect('locked_users')


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

    # ── ข้อมูลที่ทุก role เห็น: วันหยุดบริษัท + ปฏิทินลาตัวเอง ──
    user = request.user
    from datetime import date as date_cls, timedelta
    from attendance.models import CompanyHoliday
    from leave.models import LeaveRequest as LR

    today = timezone.localdate()

    # รองรับ ?month=YYYY-MM เพื่อให้เลื่อนดูเดือนได้
    month_str = request.GET.get('month', '')
    try:
        from datetime import datetime as dt_cls
        cal_date = dt_cls.strptime(month_str, '%Y-%m').date() if month_str else today
    except ValueError:
        cal_date = today

    month_start = cal_date.replace(day=1)
    month_end = cal_date.replace(day=calendar.monthrange(cal_date.year, cal_date.month)[1])

    # ลิงก์เดือนก่อน/ถัดไป
    prev_month = (month_start - timedelta(days=1)).replace(day=1)
    next_month = (month_end + timedelta(days=1)).replace(day=1)
    context['cal_prev'] = prev_month.strftime('%Y-%m')
    context['cal_next'] = next_month.strftime('%Y-%m')
    context['cal_is_current'] = (cal_date.year == today.year and cal_date.month == today.month)

    # วันหยุดทั้งปี (ทุก role เห็น)
    context['holidays_year'] = list(
        CompanyHoliday.objects.filter(date__year=cal_date.year).order_by('date')
    )
    context['calendar_month'] = cal_date

    # ปฏิทินลาส่วนตัวของ user คนนี้ (employee หรือ manager ก็เห็นของตัวเอง)
    my_approved_leaves = LR.objects.filter(
        employee=user,
        status='approved',
        start_date__lte=month_end,
        end_date__gte=month_start,
    ).select_related('leave_type').order_by('start_date')

    holidays_this_month = {
        h.date: h for h in CompanyHoliday.objects.filter(
            date__year=cal_date.year, date__month=cal_date.month
        )
    }
    num_days = month_end.day
    my_days = []
    for day in range(1, num_days + 1):
        d = date_cls(cal_date.year, cal_date.month, day)
        on_leave = [lr for lr in my_approved_leaves if lr.start_date <= d <= lr.end_date]
        my_days.append({
            'date': d,
            'weekday': d.weekday(),
            'is_today': d == today,
            'on_leave': on_leave,
            'holiday': holidays_this_month.get(d),
        })
    context['my_calendar_days'] = my_days
    context['my_calendar_empty_prefix'] = list(range(month_start.weekday()))

    # Manager-specific: pending approvals from direct reports + monthly leave calendar
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

            # Monthly leave calendar — approved leaves for selected month
            approved_leaves = LeaveRequest.objects.filter(
                employee__in=direct_reports,
                status='approved',
                start_date__lte=month_end,
                end_date__gte=month_start,
            ).select_related('employee', 'leave_type').order_by('start_date')

            # Build calendar days list
            num_days = month_end.day
            days_data = []
            for day in range(1, num_days + 1):
                d = date_cls(cal_date.year, cal_date.month, day)
                on_leave = []
                for lr in approved_leaves:
                    if lr.start_date <= d <= lr.end_date:
                        on_leave.append(lr)
                holiday = holidays_this_month.get(d)
                days_data.append({
                    'date': d,
                    'weekday': d.weekday(),
                    'is_today': d == today,
                    'on_leave': on_leave,
                    'on_leave_extra': max(0, len(on_leave) - 2),
                    'holiday': holiday,
                })
            # Pad the start of the grid (Monday = 0)
            first_offset = month_start.weekday()
            empty_prefix = list(range(first_offset))
            context['calendar_days'] = days_data
            context['calendar_empty_prefix'] = empty_prefix

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
def user_change_role(request, pk):
    if not request.user.is_super_admin:
        messages.error(request, 'Permission denied.')
        return redirect('user_list')
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        if user.pk == request.user.pk:
            messages.error(request, 'Cannot change your own role.')
            return redirect('user_list')
        new_role = request.POST.get('role')
        if new_role in ('admin', 'manager', 'employee'):
            user.role = new_role
            user.save()
            messages.success(request, f'Role updated to {user.get_role_display()} for {user.get_full_name() or user.username}.')
        else:
            messages.error(request, 'Invalid role.')
    return redirect('user_list')


@login_required
def invite_user(request):
    if is_rate_limited(request, key='ip', rate='10/h', method='POST'):
        return HttpResponse('สร้างบัญชีบ่อยเกินไป กรุณารอ 1 ชั่วโมง', status=429)
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
