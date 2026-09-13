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
            from datetime import datetime, time as dtime, date as ddate
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active

            errors = []
            records_to_upsert = []

            # Pre-load employee lookup caches (avoids N+1 queries)
            try:
                from employees.models import EmployeeProfile
                emp_by_id = {p.employee_id: p.user for p in EmployeeProfile.objects.select_related('user').all()}
            except Exception:
                emp_by_id = {}
            emp_by_username = {u.username: u for u in User.objects.all()}
            emp_by_email = {u.email: u for u in User.objects.all() if u.email}

            def resolve_employee(key):
                key = str(key).strip()
                if key in emp_by_id:
                    return emp_by_id[key]
                if key in emp_by_username:
                    return emp_by_username[key]
                if key in emp_by_email:
                    return emp_by_email[key]
                raise User.DoesNotExist(key)

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

            def calc_hours(ci, co):
                if ci and co:
                    diff = datetime.combine(ddate.today(), co) - datetime.combine(ddate.today(), ci)
                    if diff.total_seconds() > 0:
                        return round(diff.total_seconds() / 3600, 2)
                return 0

            valid_statuses = {s for s, _ in AttendanceRecord.STATUS_CHOICES}

            # Expected columns: employee_id/username/email, date, clock_in, clock_out, status
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):
                    continue
                try:
                    username_or_email, date_val, clock_in_val, clock_out_val, status_val = (
                        row[0], row[1], row[2], row[3], row[4] if len(row) > 4 else 'present'
                    )
                    employee = resolve_employee(username_or_email)
                    record_date = datetime.strptime(date_val, '%Y-%m-%d').date() if isinstance(date_val, str) else date_val
                    clock_in = parse_time(clock_in_val)
                    clock_out = parse_time(clock_out_val)
                    status = (status_val or 'present').strip().lower()
                    if status not in valid_statuses:
                        status = 'present'
                    records_to_upsert.append(AttendanceRecord(
                        employee=employee,
                        date=record_date,
                        clock_in=clock_in,
                        clock_out=clock_out,
                        status=status,
                        work_hours=calc_hours(clock_in, clock_out),
                    ))
                except User.DoesNotExist:
                    errors.append(f"Row {row_num}: user '{row[0]}' not found.")
                except Exception as e:
                    errors.append(f"Row {row_num}: {e}")

            # Single bulk upsert — uses INSERT ... ON CONFLICT DO UPDATE (no per-row transactions)
            if records_to_upsert:
                AttendanceRecord.objects.bulk_create(
                    records_to_upsert,
                    update_conflicts=True,
                    update_fields=['clock_in', 'clock_out', 'status', 'work_hours', 'updated_at'],
                    unique_fields=['employee', 'date'],
                )
            created = len(records_to_upsert)

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


# ─── Attendance list export ───────────────────────────────────────────────────

@login_required
def attendance_list_export(request):
    """HR/Admin: export attendance records for the selected month as Excel (import-ready format)."""
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('attendance_dashboard')

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse

    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    records = AttendanceRecord.objects.filter(
        date__year=year, date__month=month
    ).select_related('employee', 'employee__employee_profile').order_by('date', 'employee__first_name')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'{year}-{month:02d}'

    # Styles
    header_font = Font(bold=True, color='FFFFFF', size=10)
    header_fill = PatternFill('solid', fgColor='152057')
    center = Alignment(horizontal='center', vertical='center')
    left = Alignment(horizontal='left', vertical='center')
    thin = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB'),
    )

    # Header row — matches import template columns exactly
    headers = ['employee_id', 'date (YYYY-MM-DD)', 'clock_in (HH:MM)', 'clock_out (HH:MM)', 'status', 'ชื่อพนักงาน (อ้างอิงเท่านั้น)']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center if col < 6 else left
        cell.border = thin
    ws.row_dimensions[1].height = 22

    # Data rows
    alt_fill = PatternFill('solid', fgColor='F9FAFB')
    for row_idx, r in enumerate(records, 2):
        try:
            emp_code = r.employee.employee_profile.employee_id or r.employee.username
        except Exception:
            emp_code = r.employee.username

        clock_in_str = r.clock_in.strftime('%H:%M') if r.clock_in else ''
        clock_out_str = r.clock_out.strftime('%H:%M') if r.clock_out else ''

        row_data = [
            emp_code,
            r.date.strftime('%Y-%m-%d'),
            clock_in_str,
            clock_out_str,
            r.status,
            r.employee.get_full_name() or r.employee.username,
        ]
        fill = alt_fill if row_idx % 2 == 0 else None
        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            cell.border = thin
            cell.alignment = left
            if fill:
                cell.fill = fill

    # Column widths
    for i, w in enumerate([18, 18, 16, 16, 12, 28], 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="attendance_{year}-{month:02d}.xlsx"'
    wb.save(response)
    return response


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

    employees = User.objects.filter(is_active=True, is_superuser=False).select_related('employee_profile').order_by('first_name', 'last_name')

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
        # cap regular work hours at 8 hrs/day; extra hours are OT (tracked separately)
        att_by_emp[eid]['work_hours'] += min(float(r['work_hours'] or 0), 8.0)

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
        try:
            emp_code = emp.employee_profile.employee_id or '—'
        except Exception:
            emp_code = '—'
        summary.append({
            'emp': emp,
            'employee_id': emp_code,
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


@login_required
def payroll_export(request):
    """Export payroll summary as Excel (.xlsx)."""
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('attendance_dashboard')

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    from leave.models import LeaveRequest, LeaveType
    from overtime.models import OTRequest
    import calendar

    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    employees = User.objects.filter(is_active=True, is_superuser=False).select_related('employee_profile').order_by('first_name', 'last_name')

    att_records = AttendanceRecord.objects.filter(
        date__year=year, date__month=month
    ).values('employee_id', 'status', 'work_hours')
    att_by_emp = {}
    for r in att_records:
        eid = r['employee_id']
        if eid not in att_by_emp:
            att_by_emp[eid] = {'present': 0, 'late': 0, 'absent': 0, 'wfh': 0, 'half_day': 0, 'work_hours': 0}
        att_by_emp[eid][r['status']] = att_by_emp[eid].get(r['status'], 0) + 1
        att_by_emp[eid]['work_hours'] += min(float(r['work_hours'] or 0), 8.0)

    from datetime import date as date_cls
    month_start = date_cls(year, month, 1)
    month_end = date_cls(year, month, calendar.monthrange(year, month)[1])
    leave_qs = LeaveRequest.objects.filter(
        status='approved', start_date__year=year, start_date__month=month,
    ).select_related('leave_type').values('employee_id', 'leave_type__name', 'start_date', 'end_date')
    leave_by_emp = {}
    for lr in leave_qs:
        eid = lr['employee_id']
        if eid not in leave_by_emp:
            leave_by_emp[eid] = []
        start = max(lr['start_date'], month_start)
        end = min(lr['end_date'], month_end)
        days = max(0, (end - start).days + 1)
        leave_by_emp[eid].append({'leave_type': lr['leave_type__name'], 'days': days})

    ot_qs = OTRequest.objects.filter(
        status='approved', date__year=year, date__month=month,
    ).values('employee_id').annotate(total_ot=Sum('hours'))
    ot_by_emp = {r['employee_id']: float(r['total_ot'] or 0) for r in ot_qs}

    # Build workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'{year}-{month:02d}'

    # Styles
    header_font = Font(bold=True, color='FFFFFF', size=10)
    header_fill = PatternFill('solid', fgColor='152057')
    center = Alignment(horizontal='center', vertical='center')
    thin = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB'),
    )

    # Title row
    ws.merge_cells('A1:L1')
    title_cell = ws['A1']
    title_cell.value = f'สรุปข้อมูลสำหรับคำนวณเงินเดือน — {year}-{month:02d}'
    title_cell.font = Font(bold=True, size=13, color='152057')
    title_cell.alignment = center
    ws.row_dimensions[1].height = 28

    # Header row
    headers = ['พนักงาน', 'รหัสพนักงาน', 'แผนก', 'มา (วัน)', 'WFH', 'มาสาย', 'ขาด', 'ครึ่งวัน', 'ลา (วัน)', 'ชม.งาน', 'OT (ชม.)', 'ประเภทลา']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = thin
    ws.row_dimensions[2].height = 22

    # Data rows
    for row_idx, emp in enumerate(employees, 3):
        att = att_by_emp.get(emp.pk, {})
        leave_items = leave_by_emp.get(emp.pk, [])
        total_leave = sum(li['days'] for li in leave_items)
        ot_hours = ot_by_emp.get(emp.pk, 0)
        present = att.get('present', 0) + att.get('late', 0) + att.get('wfh', 0)
        leave_str = ', '.join(f"{li['leave_type']} {li['days']}ว." for li in leave_items) or '—'
        try:
            emp_code = emp.employee_profile.employee_id or '—'
        except Exception:
            emp_code = '—'

        row_data = [
            emp.get_full_name() or emp.username,
            emp_code,
            emp.department or '—',
            present,
            att.get('wfh', 0),
            att.get('late', 0),
            att.get('absent', 0),
            att.get('half_day', 0),
            total_leave,
            round(att.get('work_hours', 0), 2),
            round(ot_hours, 2),
            leave_str,
        ]
        alt_fill = PatternFill('solid', fgColor='F9FAFB') if row_idx % 2 == 0 else None
        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            cell.border = thin
            cell.alignment = Alignment(horizontal='left' if col in (1, 3) else 'center', vertical='center')
            if alt_fill:
                cell.fill = alt_fill

    # Column widths
    col_widths = [22, 13, 16, 9, 7, 7, 7, 9, 9, 10, 10, 40]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="payroll_{year}-{month:02d}.xlsx"'
    wb.save(response)
    return response
