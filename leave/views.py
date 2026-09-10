from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import LeaveType, LeaveBalance, LeaveRequest
from .forms import LeaveRequestForm, ReviewForm, LeaveTypeForm, LeaveBalanceForm


def _get_approvable_requests(user):
    """Return queryset of pending requests this user can approve."""
    if user.is_hr_or_admin:
        return LeaveRequest.objects.filter(status='pending')
    elif user.can_approve:
        # Manager: เห็นเฉพาะคำขอของลูกน้องที่ยัง pending
        direct_report_users = user.get_direct_report_users()
        return LeaveRequest.objects.filter(
            status='pending', employee__in=direct_report_users
        )
    return LeaveRequest.objects.none()


@login_required
def leave_dashboard(request):
    year = timezone.now().year
    my_requests = LeaveRequest.objects.filter(employee=request.user).order_by('-created_at')[:5]
    my_balances = LeaveBalance.objects.filter(
        employee=request.user, year=year
    ).select_related('leave_type')

    pending_count = _get_approvable_requests(request.user).count()

    return render(request, 'leave/dashboard.html', {
        'my_requests': my_requests,
        'my_balances': my_balances,
        'pending_count': pending_count,
        'year': year,
    })


@login_required
def request_list(request):
    user = request.user
    if user.is_hr_or_admin:
        requests = LeaveRequest.objects.select_related('employee', 'leave_type').all()
    elif user.is_manager:
        # Manager เห็นของตัวเองและลูกน้อง
        direct_report_users = user.get_direct_report_users()
        requests = LeaveRequest.objects.filter(
            Q(employee=user) | Q(employee__in=direct_report_users)
        ).select_related('employee', 'leave_type')
    else:
        requests = LeaveRequest.objects.filter(employee=user)

    status = request.GET.get('status')
    if status:
        requests = requests.filter(status=status)

    requests = requests.order_by('-created_at')

    return render(request, 'leave/request_list.html', {
        'requests': requests,
        'status_choices': LeaveRequest.STATUS_CHOICES,
        'status_filter': status,
    })


@login_required
def request_create(request):
    form = LeaveRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        req = form.save(commit=False)
        req.employee = request.user
        req.save()
        messages.success(request, 'ส่งคำขอลาเรียบร้อย รอการอนุมัติจากหัวหน้า')
        return redirect('leave_list')
    return render(request, 'leave/request_form.html', {'form': form, 'title': 'ขอลา'})


@login_required
def request_detail(request, pk):
    req = get_object_or_404(LeaveRequest, pk=pk)
    user = request.user

    # ตรวจสิทธิ์ดู
    if not user.is_hr_or_admin:
        if req.employee != user and not user.is_manager_of(req.employee):
            messages.error(request, 'ไม่มีสิทธิ์เข้าถึง')
            return redirect('leave_list')

    # ตรวจสิทธิ์ approve (hr/admin หรือหัวหน้าตรงของพนักงานคนนั้น)
    can_review = (
        req.status == 'pending'
        and (
            user.is_hr_or_admin
            or (user.can_approve and user.is_manager_of(req.employee))
        )
    )
    review_form = ReviewForm(instance=req) if can_review else None

    if request.method == 'POST' and can_review:
        review_form = ReviewForm(request.POST, instance=req)
        if review_form.is_valid():
            r = review_form.save(commit=False)
            r.approved_by = user
            r.approved_at = timezone.now()
            r.reviewed_by = user
            r.reviewed_at = timezone.now()
            r.save()
            if r.status == 'approved':
                bal, _ = LeaveBalance.objects.get_or_create(
                    employee=r.employee, leave_type=r.leave_type,
                    year=r.start_date.year,
                    defaults={'entitled_days': r.leave_type.days_per_year or r.leave_type.default_days}
                )
                bal.used_days += r.days
                bal.save()
                messages.success(request, 'อนุมัติคำขอลาเรียบร้อย')
            else:
                messages.warning(request, 'ไม่อนุมัติคำขอลา')
            return redirect('leave_list')

    # Leave balance ของพนักงานคนนั้น
    year = req.start_date.year if req.start_date else timezone.now().year
    try:
        balance = LeaveBalance.objects.get(
            employee=req.employee,
            leave_type=req.leave_type,
            year=year,
        )
    except LeaveBalance.DoesNotExist:
        balance = None

    return render(request, 'leave/request_detail.html', {
        'req': req,
        'review_form': review_form,
        'can_review': can_review,
        'balance': balance,
    })


@login_required
def request_cancel(request, pk):
    req = get_object_or_404(LeaveRequest, pk=pk, employee=request.user)
    if req.status == 'pending':
        req.status = 'cancelled'
        req.save()
        messages.success(request, 'ยกเลิกคำขอเรียบร้อย')
    return redirect('leave_list')


@login_required
def leave_type_list(request):
    if not request.user.is_hr_or_admin:
        return redirect('leave_dashboard')
    types = LeaveType.objects.all()
    form = LeaveTypeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'เพิ่มประเภทการลาเรียบร้อย')
        return redirect('leave_type_list')
    return render(request, 'leave/type_list.html', {'types': types, 'form': form})


@login_required
def balance_list(request):
    if not request.user.is_hr_or_admin:
        return redirect('leave_dashboard')
    year = request.GET.get('year', timezone.now().year)
    balances = LeaveBalance.objects.filter(year=year).select_related(
        'employee', 'leave_type'
    ).order_by('employee__first_name')
    form = LeaveBalanceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'บันทึกวันลาเรียบร้อย')
        return redirect('leave_balance_list')
    return render(request, 'leave/balance_list.html', {
        'balances': balances,
        'form': form,
        'year': year,
    })
