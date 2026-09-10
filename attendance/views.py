from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from .models import AttendanceRecord
from .forms import AttendanceForm, AttendanceAdminForm


@login_required
def attendance_dashboard(request):
    today = timezone.localdate()
    year = today.year
    month = today.month

    # Today's record for current user
    today_record = AttendanceRecord.objects.filter(
        employee=request.user, date=today
    ).first()

    # This month's records
    monthly = AttendanceRecord.objects.filter(
        employee=request.user, date__year=year, date__month=month
    )
    total_days = monthly.count()
    present_days = monthly.filter(status__in=['present', 'wfh']).count()
    late_days = monthly.filter(status='late').count()
    total_hours = monthly.aggregate(t=Sum('work_hours'))['t'] or 0

    return render(request, 'attendance/dashboard.html', {
        'today_record': today_record,
        'today': today,
        'total_days': total_days,
        'present_days': present_days,
        'late_days': late_days,
        'total_hours': total_hours,
        'month_name': today.strftime('%B %Y'),
    })


@login_required
def attendance_checkin(request):
    """Employee self-entry: add or edit today's attendance."""
    today = timezone.localdate()
    record = AttendanceRecord.objects.filter(employee=request.user, date=today).first()
    form = AttendanceForm(request.POST or None, instance=record,
                          initial={'date': today})
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.employee = request.user
        obj.save()
        messages.success(request, 'Attendance recorded.')
        return redirect('attendance_dashboard')
    return render(request, 'attendance/checkin_form.html', {
        'form': form, 'record': record, 'today': today
    })


@login_required
def attendance_my_report(request):
    """Monthly report for the logged-in employee."""
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    records = AttendanceRecord.objects.filter(
        employee=request.user, date__year=year, date__month=month
    ).order_by('date')
    total_hours = records.aggregate(t=Sum('work_hours'))['t'] or 0
    return render(request, 'attendance/my_report.html', {
        'records': records,
        'year': year,
        'month': month,
        'total_hours': total_hours,
        'status_choices': AttendanceRecord.STATUS_CHOICES,
    })


@login_required
def attendance_list(request):
    """HR/Admin: view all attendance records."""
    if not request.user.is_hr_or_admin:
        return redirect('attendance_dashboard')
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    records = AttendanceRecord.objects.filter(
        date__year=year, date__month=month
    ).select_related('employee').order_by('date', 'employee__first_name')

    form = AttendanceAdminForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Attendance record saved.')
        return redirect('attendance_list')

    return render(request, 'attendance/attendance_list.html', {
        'records': records,
        'year': year,
        'month': month,
        'form': form,
    })


@login_required
def attendance_edit(request, pk):
    record = get_object_or_404(AttendanceRecord, pk=pk)
    if not request.user.is_hr_or_admin and record.employee != request.user:
        return redirect('attendance_dashboard')
    if request.user.is_hr_or_admin:
        form = AttendanceAdminForm(request.POST or None, instance=record)
    else:
        form = AttendanceForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Attendance updated.')
        return redirect('attendance_list' if request.user.is_hr_or_admin else 'attendance_my_report')
    return render(request, 'attendance/checkin_form.html', {
        'form': form, 'record': record
    })
