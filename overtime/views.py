from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import OTRequest
from .forms import OTRequestForm, OTReviewForm


@login_required
def ot_dashboard(request):
    my_requests = OTRequest.objects.filter(employee=request.user)[:5]
    pending_count = OTRequest.objects.filter(status='pending').count() if request.user.is_hr_or_admin else 0
    return render(request, 'overtime/dashboard.html', {
        'my_requests': my_requests,
        'pending_count': pending_count,
    })


@login_required
def ot_list(request):
    if request.user.is_hr_or_admin:
        requests = OTRequest.objects.select_related('employee').all()
    else:
        requests = OTRequest.objects.filter(employee=request.user)
    status = request.GET.get('status')
    if status:
        requests = requests.filter(status=status)
    return render(request, 'overtime/ot_list.html', {
        'requests': requests,
        'status_choices': OTRequest.STATUS_CHOICES,
        'status_filter': status,
    })


@login_required
def ot_create(request):
    form = OTRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        req = form.save(commit=False)
        req.employee = request.user
        req.save()
        messages.success(request, 'OT request submitted.')
        return redirect('ot_list')
    return render(request, 'overtime/ot_form.html', {'form': form, 'title': 'Request OT'})


@login_required
def ot_detail(request, pk):
    req = get_object_or_404(OTRequest, pk=pk)
    can_review = request.user.is_hr_or_admin and req.status == 'pending'
    review_form = OTReviewForm(instance=req) if can_review else None

    if request.method == 'POST' and can_review:
        review_form = OTReviewForm(request.POST, instance=req)
        if review_form.is_valid():
            r = review_form.save(commit=False)
            r.reviewed_by = request.user
            r.reviewed_at = timezone.now()
            r.save()
            messages.success(request, f'OT request {r.status}.')
            return redirect('ot_list')

    return render(request, 'overtime/ot_detail.html', {
        'req': req, 'review_form': review_form, 'can_review': can_review
    })


@login_required
def ot_cancel(request, pk):
    req = get_object_or_404(OTRequest, pk=pk, employee=request.user)
    if req.status == 'pending':
        req.status = 'cancelled'
        req.save()
        messages.success(request, 'OT request cancelled.')
    return redirect('ot_list')
