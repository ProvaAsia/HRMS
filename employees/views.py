from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import EmployeeProfile, Department, Division
from .forms import EmployeeProfileForm


@login_required
def employee_list(request):
    """
    super_admin / hr_manager : เห็นทุกคน + มีสิทธิ์แก้ไข
    manager                  : เห็นแค่ทีมของตัวเอง (read-only)
    employee                 : redirect ไป my_profile
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
        # Manager เห็นตัวเองเป็น banner และลูกน้องเป็น card grid (read-only)
        try:
            mgr_profile = user.employee_profile
            subordinate_profiles = EmployeeProfile.objects.filter(
                direct_manager=mgr_profile
            ).select_related('user', 'department', 'division').order_by('first_name_en')
        except EmployeeProfile.DoesNotExist:
            mgr_profile = None
            subordinate_profiles = EmployeeProfile.objects.none()

        return render(request, 'employees/list.html', {
            'is_manager_view': True,
            'mgr_profile': mgr_profile,
            'subordinate_profiles': subordinate_profiles,
            'departments': Department.objects.all(),
            'employment_types': EmployeeProfile.EMPLOYMENT_TYPE_CHOICES,
            'can_edit': False,
        })

    else:
        return redirect('employee_my_profile')


@login_required
def employee_detail(request, pk):
    profile = get_object_or_404(EmployeeProfile, pk=pk)
    user = request.user

    # super_admin / hr_manager → ดูได้ทุกคน
    # manager → ดูได้เฉพาะตัวเองและลูกน้อง
    # employee → ดูได้แค่ตัวเอง
    if user.is_hr_or_admin:
        can_edit = True
    elif user.is_manager:
        if profile.user == user or user.is_manager_of(profile.user):
            can_edit = False
        else:
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

    return render(request, 'employees/detail.html', {
        'profile': profile,
        'can_edit': can_edit,
        'subordinates': subordinates,
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
    try:
        profile = request.user.employee_profile
    except EmployeeProfile.DoesNotExist:
        profile = None
    return render(request, 'employees/my_profile.html', {'profile': profile})


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
