from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import LeaveType, LeaveBalance, LeaveRequest
from .forms import LeaveRequestForm, ReviewForm, LeaveTypeForm, LeaveBalanceForm


@login_required
def leave_dashboard(request):
    year = timezone.now().year
    my_requests = LeaveRequest.objects.filter(employee=request.user).order_by('-created_at')[:5]
    my_balances = LeaveBalance.objects.filter(employee=request.user, year=year).select_related('leave_type')
    pending_count = LeaveRequest.objects.filter(status='pending').count() if request.user.is_hr_or_admin else 0
    return render(request, 'leave/dashboard.html', {
        'my_requests': my_requests,
        'my_balances': my_balances,
        'pending_count': pending_count,
        'year': year,
    })


@login_required
def request_list(request):
    if request.user.is_hr_or_admin:
        requests = LeaveRequest.objects.select_related('employee', 'leave_type').all()
    else:
        requests = LeaveRequest.objects.filter(employee=request.user)
    status = request.GET.get('status')
    if status:
        requests = requests.filter(status=status)
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
        messages.success(request, 'Leave request submitted.')
        return redirect('leave_list')
    return render(request, 'leave/request_form.html', {'form': form, 'title': 'Request Leave'})


@login_required
def request_detail(request, pk):
    req = get_object_or_404(LeaveRequest, pk=pk)
    can_review = request.user.is_hr_or_admin and req.status == 'pending'
    review_form = ReviewForm(instance=req) if can_review else None

    if request.method == 'POST' and can_review:
        review_form = ReviewForm(request.POST, instance=req)
        if review_form.is_valid():
            r = review_form.save(commit=False)
            r.reviewed_by = request.user
            r.reviewed_at = timezone.now()
            r.save()
            # Update balance if approved
            if r.status == 'approved':
                bal, _ = LeaveBalance.objects.get_or_create(
                    employee=r.employee, leave_type=r.leave_type,
                    year=r.start_date.year,
                    defaults={'entitled_days': r.leave_type.days_per_year}
                )
                bal.used_days += r.days
                bal.save()
            messages.success(request, f'Request {r.status}.')
            return redirect('leave_list')

    return render(request, 'leave/request_detail.html', {
        'req': req, 'review_form': review_form, 'can_review': can_review
    })


@login_required
def request_cancel(request, pk):
    req = get_object_or_404(LeaveRequest, pk=pk, employee=request.user)
    if req.status == 'pending':
        req.status = 'cancelled'
        req.save()
        messages.success(request, 'Request cancelled.')
    return redirect('leave_list')


@login_required
def leave_type_list(request):
    if not request.user.is_hr_or_admin:
        return redirect('leave_dashboard')
    types = LeaveType.objects.all()
    form = LeaveTypeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Leave type created.')
        return redirect('leave_type_list')
    return render(request, 'leave/type_list.html', {'types': types, 'form': form})


@login_required
def balance_list(request):
    if not request.user.is_hr_or_admin:
        return redirect('leave_dashboard')
    year = request.GET.get('year', timezone.now().year)
    balances = LeaveBalance.objects.filter(year=year).select_related('employee', 'leave_type').order_by('employee__first_name')
    form = LeaveBalanceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Balance set.')
        return redirect('leave_balance_list')
    return render(request, 'leave/balance_list.html', {'balances': balances, 'form': form, 'year': year})
