from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum
from .models import OTRequest
from .forms import OTRequestForm, OTReviewForm


def _get_approvable_ot(user):
    """Return queryset of pending OT requests this user can approve."""
    if user.is_hr_or_admin:
        return OTRequest.objects.filter(status='pending')
    elif user.can_approve:
        direct_report_users = user.get_direct_report_users()
        return OTRequest.objects.filter(
            status='pending', employee__in=direct_report_users
        )
    return OTRequest.objects.none()


@login_required
def ot_dashboard(request):
    now = timezone.now()
    my_requests = OTRequest.objects.filter(employee=request.user)[:5]
    pending_count = _get_approvable_ot(request.user).count()

    # ชั่วโมง OT ที่ approved ในเดือนปัจจุบัน
    monthly_hours = OTRequest.objects.filter(
        employee=request.user,
        status='approved',
        date__year=now.year,
        date__month=now.month,
    ).aggregate(total=Sum('hours'))['total'] or 0

    return render(request, 'overtime/dashboard.html', {
        'my_requests': my_requests,
        'pending_count': pending_count,
        'monthly_hours': monthly_hours,
        'current_month': now.strftime('%B %Y'),
    })


@login_required
def ot_list(request):
    user = request.user
    if user.is_hr_or_admin:
        requests = OTRequest.objects.select_related('employee').all()
    elif user.is_manager:
        direct_report_users = user.get_direct_report_users()
        requests = OTRequest.objects.filter(
            Q(employee=user) | Q(employee__in=direct_report_users)
        ).select_related('employee')
    else:
        requests = OTRequest.objects.filter(employee=user)

    status = request.GET.get('status')
    if status:
        requests = requests.filter(status=status)

    requests = requests.order_by('-created_at')

    # สรุป OT รายเดือน (เฉพาะ approved)
    now = timezone.now()
    monthly_summary = OTRequest.objects.filter(
        employee=request.user,
        status='approved',
        date__year=now.year,
        date__month=now.month,
    ).aggregate(total=Sum('hours'))['total'] or 0

    return render(request, 'overtime/ot_list.html', {
        'requests': requests,
        'status_choices': OTRequest.STATUS_CHOICES,
        'status_filter': status,
        'monthly_hours': monthly_summary,
        'current_month': now.strftime('%B %Y'),
    })


@login_required
def ot_create(request):
    form = OTRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        req = form.save(commit=False)
        req.employee = request.user
        req.save()
        messages.success(request, 'ส่งคำขอโอทีเรียบร้อย รอการอนุมัติจากหัวหน้า')
        return redirect('ot_list')
    return render(request, 'overtime/ot_form.html', {'form': form, 'title': 'ขอโอที'})


@login_required
def ot_detail(request, pk):
    req = get_object_or_404(OTRequest, pk=pk)
    user = request.user

    # ตรวจสิทธิ์ดู
    if not user.is_hr_or_admin:
        if req.employee != user and not user.is_manager_of(req.employee):
            messages.error(request, 'ไม่มีสิทธิ์เข้าถึง')
            return redirect('ot_list')

    # ตรวจสิทธิ์ approve
    can_review = (
        req.status == 'pending'
        and (
            user.is_hr_or_admin
            or (user.can_approve and user.is_manager_of(req.employee))
        )
    )
    review_form = OTReviewForm(instance=req) if can_review else None

    if request.method == 'POST' and can_review:
        review_form = OTReviewForm(request.POST, instance=req)
        if review_form.is_valid():
            r = review_form.save(commit=False)
            r.reviewed_by = user
            r.reviewed_at = timezone.now()
            r.save()
            if r.status == 'approved':
                messages.success(request, 'อนุมัติโอทีเรียบร้อย')
            else:
                messages.warning(request, 'ไม่อนุมัติโอที')
            return redirect('ot_list')

    return render(request, 'overtime/ot_detail.html', {
        'req': req,
        'review_form': review_form,
        'can_review': can_review,
    })


@login_required
def ot_cancel(request, pk):
    req = get_object_or_404(OTRequest, pk=pk, employee=request.user)
    if req.status == 'pending':
        req.status = 'cancelled'
        req.save()
        messages.success(request, 'ยกเลิกคำขอโอทีเรียบร้อย')
    return redirect('ot_list')
