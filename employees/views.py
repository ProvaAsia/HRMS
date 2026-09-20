import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum

from .models import EmployeeProfile, Department, Division
from .forms import EmployeeProfileForm


@login_required
def employee_list(request):
    """
    admin    : เห็นทุกคน + มีสิทธิ์แก้ไข
    manager  : เห็นแค่ทีมของตัวเอง (read-only)
    employee : redirect ไป my_profile
    """
    user = request.user

    if user.is_hr_or_admin:
        profiles = EmployeeProfile.objects.select_related(
            'user', 'department', 'division', 'work_location'
        ).order_by('employee_id')

        q = request.GET.get('q', '').strip()
        dept = request.GET.get('department', '')
        emp_type = request.GET.get('employment_type', '')

        if q:
            profiles = profiles.filter(
                Q(employee_id__icontains=q) |
                Q(first_name_en__icontains=q) |
                Q(last_name_en__icontains=q) |
                Q(first_name_th__icontains=q) |
                Q(last_name_th__icontains=q) |
                Q(job_title__icontains=q)
            )
        if dept:
            profiles = profiles.filter(department_id=dept)
        if emp_type:
            profiles = profiles.filter(employment_type=emp_type)

        departments = Department.objects.all()
        employment_types = EmployeeProfile.EMPLOYMENT_TYPE_CHOICES

        return render(request, 'employees/list.html', {
            'profiles': profiles,
            'departments': departments,
            'employment_types': employment_types,
            'q': q,
            'selected_dept': dept,
            'selected_type': emp_type,
            'can_edit': True,
        })

    elif user.is_manager:
        # Manager ไปที่ profile ตัวเองโดยตรง
        try:
            mgr_profile = user.employee_profile
            return redirect('employee_detail', pk=mgr_profile.pk)
        except EmployeeProfile.DoesNotExist:
            return redirect('dashboard')

    else:
        # Employee ไปที่ profile ตัวเองโดยตรง (หน้า detail เต็ม)
        try:
            emp_profile = user.employee_profile
            return redirect('employee_detail', pk=emp_profile.pk)
        except EmployeeProfile.DoesNotExist:
            return redirect('dashboard')


@login_required
def employee_detail(request, pk):
    profile = get_object_or_404(EmployeeProfile, pk=pk)
    user = request.user

    # admin → ดูได้ทุกคน
    # manager → ดูได้เฉพาะตัวเองและลูกน้อง
    # employee → ดูได้แค่ตัวเอง
    if user.is_hr_or_admin:
        can_edit = True
    elif user.is_manager:
        # อนุญาต: ดูโปรไฟล์ตัวเอง หรือ direct report (เช็คผ่าน EmployeeProfile.direct_manager)
        try:
            mgr_profile = user.employee_profile
            is_own = (profile == mgr_profile)
            is_direct_report = (profile.direct_manager_id == mgr_profile.pk)
        except EmployeeProfile.DoesNotExist:
            is_own = False
            is_direct_report = False

        if not (is_own or is_direct_report):
            messages.error(request, 'ไม่มีสิทธิ์เข้าถึงข้อมูลนี้')
            return redirect('dashboard')
        can_edit = False
    else:
        if profile.user != user:
            messages.error(request, 'ไม่มีสิทธิ์เข้าถึงข้อมูลนี้')
            return redirect('dashboard')
        can_edit = False

    # Direct reports ของ profile นั้น (สำหรับแสดง Your Team)
    subordinates = EmployeeProfile.objects.filter(
        direct_manager=profile
    ).select_related('department').order_by('first_name_en')

    employee_user = profile.user
    current_year = datetime.date.today().year

    # ── Leave balances ─────────────────────────────────────────────────
    try:
        from leave.models import LeaveBalance, LeaveRequest
        leave_balances = LeaveBalance.objects.filter(
            employee=employee_user,
            year=current_year,
        ).select_related('leave_type').exclude(leave_type__is_lwp=True).order_by('leave_type__name')

        leave_pending_count = LeaveRequest.objects.filter(
            employee=employee_user,
            status='pending',
        ).count()
    except Exception:
        leave_balances = []
        leave_pending_count = 0

    # ── Latest appraisal ───────────────────────────────────────────────
    try:
        from appraisals.models import Appraisal
        latest_appraisal = (
            Appraisal.objects
            .filter(employee=employee_user)
            .select_related('cycle')
            .order_by('-cycle__start_date')
            .first()
        )
        appraisal_score_pct = 0
        if latest_appraisal and latest_appraisal.manager_rating:
            appraisal_score_pct = round(float(latest_appraisal.manager_rating) / 5 * 100)
    except Exception:
        latest_appraisal = None
        appraisal_score_pct = 0

    # ── Documents ──────────────────────────────────────────────────────
    documents = profile.employee_documents.all()

    # ── Training ───────────────────────────────────────────────────────
    try:
        from training.models import TrainingEnrollment
        training_enrollments = (
            TrainingEnrollment.objects
            .filter(employee=employee_user)
            .select_related('training')
            .order_by('-training__start_date')
        )
        completed = training_enrollments.filter(status='completed')
        total_days = sum(
            (e.training.end_date - e.training.start_date).days + 1
            for e in completed
            if e.training.end_date and e.training.start_date
        )
        training_stats = {
            'total_hours': total_days,
            'completed_count': completed.count(),
            'certificate_count': completed.filter(score__isnull=False).count(),
        }
    except Exception:
        training_enrollments = []
        training_stats = {'total_hours': 0, 'completed_count': 0, 'certificate_count': 0}

    return render(request, 'employees/detail.html', {
        'profile': profile,
        'can_edit': can_edit,
        'can_see_salary': can_edit,
        'subordinates': subordinates,
        'current_year': current_year,
        # leave
        'leave_balances': leave_balances,
        'leave_pending_count': leave_pending_count,
        # appraisal
        'latest_appraisal': latest_appraisal,
        'appraisal_score_pct': appraisal_score_pct,
        # documents
        'documents': documents,
        # training
        'training_enrollments': training_enrollments,
        'training_stats': training_stats,
    })


@login_required
def employee_create(request):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'ไม่มีสิทธิ์')
        return redirect('dashboard')
    form = EmployeeProfileForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'สร้างข้อมูลพนักงานเรียบร้อย')
        return redirect('employee_list')
    return render(request, 'employees/form.html', {
        'form': form,
        'action': 'Create',
        'title': 'เพิ่มพนักงาน',
    })


@login_required
def employee_edit(request, pk):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'ไม่มีสิทธิ์แก้ไขข้อมูล')
        return redirect('dashboard')
    profile = get_object_or_404(EmployeeProfile, pk=pk)
    form = EmployeeProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'อัปเดตข้อมูลเรียบร้อย')
        return redirect('employee_detail', pk=profile.pk)
    return render(request, 'employees/form.html', {
        'form': form,
        'profile': profile,
        'action': 'Save',
        'title': f'แก้ไข — {profile.full_name_en() or profile.employee_id}',
    })


@login_required
def employee_my_profile(request):
    """Redirect ทุก role ไปหน้า employee_detail เต็มรูปแบบ"""
    try:
        profile = request.user.employee_profile
        return redirect('employee_detail', pk=profile.pk)
    except EmployeeProfile.DoesNotExist:
        return redirect('dashboard')


@login_required
def org_chart(request):
    all_profiles = EmployeeProfile.objects.select_related(
        'department', 'division', 'direct_manager'
    ).all()

    def build_tree(profile):
        reports = [build_tree(r) for r in profile.direct_reports.all()]
        return {'profile': profile, 'reports': reports}

    roots = [
        build_tree(p)
        for p in all_profiles
        if p.direct_manager_id is None
    ]

    return render(request, 'employees/org_chart.html', {'roots': roots})
