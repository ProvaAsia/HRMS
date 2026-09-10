from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import EmployeeProfile, Department, Division
from .forms import EmployeeProfileForm


@login_required
def employee_list(request):
    """HR/admin sees all employees; regular employee sees only themselves."""
    if request.user.is_hr_or_admin:
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
        })
    else:
        # Redirect employee to their own profile
        return redirect('employee_my_profile')


@login_required
def employee_detail(request, pk):
    profile = get_object_or_404(EmployeeProfile, pk=pk)
    if not request.user.is_hr_or_admin and profile.user != request.user:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    return render(request, 'employees/detail.html', {'profile': profile})


@login_required
def employee_create(request):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    form = EmployeeProfileForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Employee profile created successfully.')
        return redirect('employee_list')
    return render(request, 'employees/form.html', {
        'form': form,
        'action': 'Create',
        'title': 'Add Employee',
    })


@login_required
def employee_edit(request, pk):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    profile = get_object_or_404(EmployeeProfile, pk=pk)
    form = EmployeeProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Employee profile updated.')
        return redirect('employee_detail', pk=profile.pk)
    return render(request, 'employees/form.html', {
        'form': form,
        'profile': profile,
        'action': 'Save',
        'title': f'Edit — {profile.full_name_en() or profile.employee_id}',
    })


@login_required
def employee_my_profile(request):
    """Employee self-service: view/edit own profile."""
    try:
        profile = request.user.employee_profile
    except EmployeeProfile.DoesNotExist:
        profile = None

    return render(request, 'employees/my_profile.html', {'profile': profile})


@login_required
def org_chart(request):
    """Build hierarchical org chart from direct_manager relationships."""
    # Find root nodes: profiles with no direct manager
    all_profiles = EmployeeProfile.objects.select_related(
        'department', 'division', 'direct_manager'
    ).all()

    # Build a dict for quick lookup
    profile_map = {p.pk: p for p in all_profiles}

    def build_tree(profile):
        reports = [build_tree(r) for r in profile.direct_reports.all()]
        return {
            'profile': profile,
            'reports': reports,
        }

    roots = [
        build_tree(p)
        for p in all_profiles
        if p.direct_manager_id is None
    ]

    return render(request, 'employees/org_chart.html', {
        'roots': roots,
    })
