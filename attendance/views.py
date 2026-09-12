from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from .models import AttendanceRecord, AttendanceCorrectionRequest
from .forms import AttendanceForm, AttendanceAdminForm
from accounts.models import User


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

    # Pending correction requests for this employee
    pending_corrections = AttendanceCorrectionRequest.objects.filter(
        employee=request.user, status='pending'
    ).count()

    # If manager: count pending corrections from direct reports
    mgr_pending_corrections = 0
    if request.user.can_approve:
        direct_reports = request.user.get_direct_report_users()
        mgr_pending_corrections = AttendanceCorrectionRequest.objects.filter(
            employee__in=direct_reports, status='pending'
        ).count()

    return render(request, 'attendance/dashboard.html', {
        'today_record': today_record,
        'today': today,
        'total_days': total_days,
        'present_days': present_days,
        'late_days': late_days,
        'total_hours': total_hours,
        'month_name': today.strftime('%B %Y'),
        'pending_corrections': pending_corrections,
        'mgr_pending_corrections': mgr_pending_corrections,
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
    """Monthly timesheet for the logged-in employee."""
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    records = AttendanceRecord.objects.filter(
        employee=request.user, date__year=year, date__month=month
    ).order_by('date')
    total_hours = records.aggregate(t=Sum('work_hours'))['t'] or 0

    # Fetch leave requests this month
    from leave.models import LeaveRequest
    leave_records = LeaveRequest.objects.filter(
        employee=request.user,
        status='approved',
        start_date__year=year,
        start_date__month=month,
    ).select_related('leave_type')

    # Fetch OT requests this month
    from overtime.models import OTRequest
    ot_records = OTRequest.objects.filter(
        employee=request.user,
        status='approved',
        date__year=year,
        date__month=month,
    )
    total_ot_hours = ot_records.aggregate(t=Sum('hours'))['t'] or 0

    # Build pending corrections map
    my_corrections = AttendanceCorrectionRequest.objects.filter(
        employee=request.user, date__year=year, date__month=month
    ).values('date', 'status')
    correction_by_date = {c['date']: c['status'] for c in my_corrections}

    return render(request, 'attendance/my_report.html', {
        'records': records,
        'year': year,
        'month': month,
        'total_hours': total_hours,
        'status_choices': AttendanceRecord.STATUS_CHOICES,
        'leave_records': leave_records,
        'ot_records': ot_records,
        'total_ot_hours': total_ot_hours,
        'correction_by_date': correction_by_date,
        'correction_items': list(correction_by_date.items()),
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


@login_required
def import_excel(request):
    """HR/Admin: upload an Excel file to bulk-import attendance records."""
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('attendance_dashboard')

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            import openpyxl
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active

            created = 0
            errors = []

            # Expected columns: username/email, date (YYYY-MM-DD), clock_in (HH:MM), clock_out (HH:MM), status
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):
                    continue
                try:
                    username_or_email, date_val, clock_in_val, clock_out_val, status_val = (
                        row[0], row[1], row[2], row[3], row[4] if len(row) > 4 else 'present'
                    )

                    # Resolve employee
                    try:
                        employee = User.objects.get(username=username_or_email)
                    except User.DoesNotExist:
                        employee = User.objects.get(email=username_or_email)

                    # Parse date
                    from datetime import datetime, time as dtime
                    if isinstance(date_val, str):
                        record_date = datetime.strptime(date_val, '%Y-%m-%d').date()
                    else:
                        record_date = date_val  # already a date from Excel

                    # Parse times
                    def parse_time(val):
                        if val is None:
                            return None
                        if isinstance(val, dtime):
                            return val
                        if hasattr(val, 'time'):
                            return val.time()
                        s = str(val).strip()
                        for fmt in ('%H:%M:%S', '%H:%M'):
                            try:
                                return datetime.strptime(s, fmt).time()
                            except ValueError:
                                pass
                        return None

                    clock_in = parse_time(clock_in_val)
                    clock_out = parse_time(clock_out_val)
                    status = (status_val or 'present').strip().lower()
                    valid_statuses = {s for s, _ in AttendanceRecord.STATUS_CHOICES}
                    if status not in valid_statuses:
                        status = 'present'

                    record, _ = AttendanceRecord.objects.update_or_create(
                        employee=employee,
                        date=record_date,
                        defaults={
                            'clock_in': clock_in,
                            'clock_out': clock_out,
                            'status': status,
                        }
                    )
                    created += 1
                except User.DoesNotExist:
                    errors.append(f"Row {row_num}: user '{row[0]}' not found.")
                except Exception as e:
                    errors.append(f"Row {row_num}: {e}")

            if errors:
                for err in errors[:10]:
                    messages.warning(request, err)
            messages.success(request, f"Import complete: {created} record(s) saved.")
        except ImportError:
            messages.error(request, 'openpyxl is not installed. Add it to requirements.txt.')
        except Exception as e:
            messages.error(request, f'Failed to read file: {e}')

        return redirect('attendance_list')

    return render(request, 'attendance/import_excel.html')


# ─── Manager: team timesheet view ─────────────────────────────────────────────

@login_required
def team_timesheet(request):
    """Manager views subordinates' timesheets; can filter by employee + month."""
    if not request.user.can_approve:
        messages.error(request, 'Permission denied.')
        return redirect('attendance_dashboard')

    direct_reports = request.user.get_direct_report_users()

    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    emp_id = request.GET.get('emp')

    selected_emp = None
    records = AttendanceRecord.objects.none()

    if emp_id:
        selected_emp = get_object_or_404(User, pk=emp_id)
        if selected_emp not in direct_reports and not request.user.is_hr_or_admin:
            messages.error(request, 'Permission denied.')
            return redirect('attendance_dashboard')
        records = AttendanceRecord.objects.filter(
            employee=selected_emp, date__year=year, date__month=month
        ).order_by('date')
    else:
        # Show summary for all direct reports
        records = AttendanceRecord.objects.filter(
            employee__in=direct_reports, date__year=year, date__month=month
        ).select_related('employee').order_by('employee__first_name', 'date')

    total_hours = records.aggregate(t=Sum('work_hours'))['t'] or 0

    # Pending correction requests from team
    pending_corrections = AttendanceCorrectionRequest.objects.filter(
        employee__in=direct_reports, status='pending'
    ).select_related('employee').order_by('-created_at')

    return render(request, 'attendance/team_timesheet.html', {
        'direct_reports': direct_reports,
        'selected_emp': selected_emp,
        'records': records,
        'year': year,
        'month': month,
        'total_hours': total_hours,
        'emp_id': emp_id,
        'pending_corrections': pending_corrections,
        'status_choices': AttendanceRecord.STATUS_CHOICES,
    })


# ─── Correction requests ──────────────────────────────────────────────────────

@login_required
def correction_request_create(request, record_pk=None):
    """Employee submits a time correction request."""
    record = None
    if record_pk:
        record = get_object_or_404(AttendanceRecord, pk=record_pk, employee=request.user)

    if request.method == 'POST':
        date_str = request.POST.get('date')
        reason = request.POST.get('reason', '').strip()
        requested_clock_in = request.POST.get('requested_clock_in') or None
        requested_clock_out = request.POST.get('requested_clock_out') or None
        requested_status = request.POST.get('requested_status') or ''

        if not date_str or not reason:
            messages.error(request, 'กรุณากรอกวันที่และเหตุผล')
        else:
            from datetime import date as date_cls
            try:
                req_date = date_cls.fromisoformat(date_str)
            except ValueError:
                messages.error(request, 'วันที่ไม่ถูกต้อง')
                return redirect('correction_request_create')

            # Find matching record if not already linked
            if not record:
                record = AttendanceRecord.objects.filter(
                    employee=request.user, date=req_date
                ).first()

            AttendanceCorrectionRequest.objects.create(
                employee=request.user,
                attendance_record=record,
                date=req_date,
                requested_clock_in=requested_clock_in or None,
                requested_clock_out=requested_clock_out or None,
                requested_status=requested_status,
                reason=reason,
            )
            messages.success(request, 'ส่งคำขอแก้ไขเวลาเรียบร้อยแล้ว รอการอนุมัติจากหัวหน้า')
            return redirect('attendance_my_report')

    today = timezone.localdate()
    return render(request, 'attendance/correction_request_form.html', {
        'record': record,
        'today': today,
        'status_choices': AttendanceRecord.STATUS_CHOICES,
    })


@login_required
def my_correction_requests(request):
    """Employee views their own correction requests."""
    corrections = AttendanceCorrectionRequest.objects.filter(
        employee=request.user
    ).select_related('attendance_record', 'reviewed_by')
    return render(request, 'attendance/my_corrections.html', {
        'corrections': corrections,
    })


@login_required
def team_correction_requests(request):
    """Manager views and acts on correction requests from direct reports."""
    if not request.user.can_approve:
        messages.error(request, 'Permission denied.')
        return redirect('attendance_dashboard')

    direct_reports = request.user.get_direct_report_users()
    corrections = AttendanceCorrectionRequest.objects.filter(
        employee__in=direct_reports
    ).select_related('employee', 'attendance_record', 'reviewed_by').order_by(
        'status', '-created_at'
    )

    return render(request, 'attendance/team_corrections.html', {
        'corrections': corrections,
    })


@login_required
def correction_request_review(request, pk):
    """Manager approves or rejects a correction request."""
    correction = get_object_or_404(AttendanceCorrectionRequest, pk=pk)

    # Check manager is authorised
    direct_reports = request.user.get_direct_report_users()
    if not request.user.is_hr_or_admin and correction.employee not in direct_reports:
        messages.error(request, 'Permission denied.')
        return redirect('attendance_dashboard')

    if correction.status != 'pending':
        messages.warning(request, 'คำขอนี้ได้รับการดำเนินการแล้ว')
        return redirect('team_correction_requests')

    if request.method == 'POST':
        action = request.POST.get('action')
        review_note = request.POST.get('review_note', '')

        if action not in ('approve', 'reject'):
            messages.error(request, 'Invalid action.')
            return redirect('team_correction_requests')

        correction.status = 'approved' if action == 'approve' else 'rejected'
        correction.reviewed_by = request.user
        correction.reviewed_at = timezone.now()
        correction.review_note = review_note
        correction.save()

        if action == 'approve' and correction.attendance_record:
            # Apply changes to the actual record
            rec = correction.attendance_record
            if correction.requested_clock_in:
                rec.clock_in = correction.requested_clock_in
            if correction.requested_clock_out:
                rec.clock_out = correction.requested_clock_out
            if correction.requested_status:
                rec.status = correction.requested_status
            rec.save()
            messages.success(request, 'อนุมัติและอัปเดตข้อมูลเวลาเรียบร้อยแล้ว')
        elif action == 'approve':
            # No existing record — create one if status/times were provided
            if correction.requested_status or correction.requested_clock_in:
                AttendanceRecord.objects.update_or_create(
                    employee=correction.employee,
                    date=correction.date,
                    defaults={
                        'clock_in': correction.requested_clock_in,
                        'clock_out': correction.requested_clock_out,
                        'status': correction.requested_status or 'present',
                    }
                )
            messages.success(request, 'อนุมัติคำขอแก้ไขเรียบร้อยแล้ว')
        else:
            messages.info(request, 'ปฏิเสธคำขอแก้ไขเรียบร้อยแล้ว')

        return redirect('team_correction_requests')

    return render(request, 'attendance/correction_review.html', {
        'correction': correction,
    })


# ─── Payroll summary ──────────────────────────────────────────────────────────

@login_required
def payroll_summary(request):
    """HR/Admin: monthly payroll-ready summary — attendance + leave + OT per employee."""
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('attendance_dashboard')

    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    from leave.models import LeaveRequest, LeaveType
    from overtime.models import OTRequest
    import calendar

    employees = User.objects.filter(role='employee').order_by('first_name', 'last_name')

    # Pre-fetch attendance aggregates per employee
    att_qs = AttendanceRecord.objects.filter(
        date__year=year, date__month=month
    ).values('employee_id').annotate(
        total_days=Sum('work_hours') - Sum('work_hours') + 0,  # count trick below
    )
    # Simpler: just pull all records and aggregate in Python
    att_records = AttendanceRecord.objects.filter(
        date__year=year, date__month=month
    ).values('employee_id', 'status', 'work_hours')

    att_by_emp = {}
    for r in att_records:
        eid = r['employee_id']
        if eid not in att_by_emp:
            att_by_emp[eid] = {'present': 0, 'late': 0, 'absent': 0, 'wfh': 0, 'half_day': 0, 'leave': 0, 'work_hours': 0}
        att_by_emp[eid][r['status']] = att_by_emp[eid].get(r['status'], 0) + 1
        att_by_emp[eid]['work_hours'] += float(r['work_hours'] or 0)

    # Leave days per employee
    leave_qs = LeaveRequest.objects.filter(
        status='approved',
        start_date__year=year,
        start_date__month=month,
    ).select_related('leave_type').values('employee_id', 'leave_type__name', 'start_date', 'end_date')

    leave_by_emp = {}
    for lr in leave_qs:
        eid = lr['employee_id']
        if eid not in leave_by_emp:
            leave_by_emp[eid] = []
        # Count days within the month
        from datetime import date as date_cls
        month_start = date_cls(year, month, 1)
        month_end = date_cls(year, month, calendar.monthrange(year, month)[1])
        start = max(lr['start_date'], month_start)
        end = min(lr['end_date'], month_end)
        days = (end - start).days + 1
        leave_by_emp[eid].append({
            'leave_type': lr['leave_type__name'],
            'days': max(0, days),
        })

    # OT hours per employee
    ot_qs = OTRequest.objects.filter(
        status='approved',
        date__year=year,
        date__month=month,
    ).values('employee_id').annotate(total_ot=Sum('hours'))
    ot_by_emp = {r['employee_id']: float(r['total_ot'] or 0) for r in ot_qs}

    # Build summary rows
    summary = []
    working_days = sum(
        1 for d in range(1, calendar.monthrange(year, month)[1] + 1)
        if calendar.weekday(year, month, d) < 5  # Mon-Fri
    )

    for emp in employees:
        att = att_by_emp.get(emp.pk, {})
        leave_items = leave_by_emp.get(emp.pk, [])
        total_leave_days = sum(li['days'] for li in leave_items)
        ot_hours = ot_by_emp.get(emp.pk, 0)
        present_days = att.get('present', 0) + att.get('late', 0) + att.get('wfh', 0)
        work_hours = att.get('work_hours', 0)
        summary.append({
            'emp': emp,
            'present_days': present_days,
            'late_days': att.get('late', 0),
            'absent_days': att.get('absent', 0),
            'wfh_days': att.get('wfh', 0),
            'half_days': att.get('half_day', 0),
            'leave_days': total_leave_days,
            'leave_items': leave_items,
            'work_hours': round(work_hours, 2),
            'ot_hours': round(ot_hours, 2),
        })

    return render(request, 'attendance/payroll_summary.html', {
        'summary': summary,
        'year': year,
        'month': month,
        'working_days': working_days,
        'month_name': f'{year}-{month:02d}',
    })
