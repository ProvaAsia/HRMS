from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TrainingProgram, TrainingEnrollment
from .forms import TrainingProgramForm, EnrollmentForm, BulkEnrollForm


def _can_manage_training(user):
    """Admin or manager can create / edit training programs."""
    return user.is_hr_or_admin or user.is_manager


@login_required
def training_list(request):
    programs = TrainingProgram.objects.all()
    status_filter = request.GET.get('status')
    if status_filter:
        programs = programs.filter(status=status_filter)
    return render(request, 'training/program_list.html', {
        'programs': programs,
        'status_choices': TrainingProgram.STATUS_CHOICES,
        'status_filter': status_filter,
    })


@login_required
def training_create(request):
    if not _can_manage_training(request.user):
        messages.error(request, 'Permission denied.')
        return redirect('training_list')

    form = TrainingProgramForm(request.POST or None)
    bulk_form = BulkEnrollForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        t = form.save(commit=False)
        t.created_by = request.user
        t.save()

        # Bulk-enroll participants chosen at creation time
        _bulk_enroll(t, bulk_form, request)

        messages.success(request, 'Training program created.')
        return redirect('training_detail', pk=t.pk)

    return render(request, 'training/program_form.html', {
        'form': form,
        'bulk_form': bulk_form,
        'title': 'Create Training Program',
    })


@login_required
def training_detail(request, pk):
    program = get_object_or_404(TrainingProgram, pk=pk)
    enrollments = program.enrollments.select_related('employee').all()
    enroll_form = EnrollmentForm()
    bulk_form = BulkEnrollForm()

    # Check if current user is already enrolled
    user_enrolled = enrollments.filter(employee=request.user).exists()

    if request.method == 'POST':
        if 'self_enroll' in request.POST:
            if not user_enrolled:
                TrainingEnrollment.objects.create(training=program, employee=request.user)
                messages.success(request, 'You have enrolled successfully.')
            return redirect('training_detail', pk=pk)

        elif 'bulk_enroll' in request.POST and _can_manage_training(request.user):
            bulk_form = BulkEnrollForm(request.POST)
            _bulk_enroll(program, bulk_form, request)
            return redirect('training_detail', pk=pk)

        elif 'single_enroll' in request.POST and _can_manage_training(request.user):
            enroll_form = EnrollmentForm(request.POST)
            if enroll_form.is_valid():
                e = enroll_form.save(commit=False)
                e.training = program
                e.save()
                messages.success(request, 'Participant enrolled.')
                return redirect('training_detail', pk=pk)

    return render(request, 'training/program_detail.html', {
        'program': program,
        'enrollments': enrollments,
        'enroll_form': enroll_form,
        'bulk_form': bulk_form,
        'user_enrolled': user_enrolled,
        'can_manage': _can_manage_training(request.user),
    })


@login_required
def training_edit(request, pk):
    if not _can_manage_training(request.user):
        messages.error(request, 'Permission denied.')
        return redirect('training_list')

    program = get_object_or_404(TrainingProgram, pk=pk)
    old_status = program.status
    form = TrainingProgramForm(request.POST or None, instance=program)

    if request.method == 'POST' and form.is_valid():
        updated = form.save()

        # Auto-complete all enrolled employees when training is marked completed
        if old_status != 'completed' and updated.status == 'completed':
            _auto_complete_enrollments(updated)

        messages.success(request, 'Training updated.')
        return redirect('training_detail', pk=pk)

    return render(request, 'training/program_form.html', {
        'form': form,
        'title': 'Edit Training',
        'object': program,
    })


@login_required
def training_delete(request, pk):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('training_list')
    program = get_object_or_404(TrainingProgram, pk=pk)
    if request.method == 'POST':
        program.delete()
        messages.success(request, 'Training deleted.')
        return redirect('training_list')
    return render(request, 'training/confirm_delete.html', {'object': program})


@login_required
def enrollment_update(request, pk):
    if not _can_manage_training(request.user):
        messages.error(request, 'Permission denied.')
        return redirect('training_list')
    enrollment = get_object_or_404(TrainingEnrollment, pk=pk)
    form = EnrollmentForm(request.POST or None, instance=enrollment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Enrollment updated.')
        return redirect('training_detail', pk=enrollment.training.pk)
    return render(request, 'training/enrollment_form.html', {'form': form, 'enrollment': enrollment})


@login_required
def enrollment_delete(request, pk):
    if not _can_manage_training(request.user):
        messages.error(request, 'Permission denied.')
        return redirect('training_list')
    enrollment = get_object_or_404(TrainingEnrollment, pk=pk)
    training_pk = enrollment.training.pk
    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, 'Enrollment removed.')
    return redirect('training_detail', pk=training_pk)


@login_required
def my_trainings(request):
    enrollments = TrainingEnrollment.objects.filter(employee=request.user).select_related('training')
    return render(request, 'training/my_trainings.html', {'enrollments': enrollments})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _bulk_enroll(program, bulk_form, request):
    """Enroll a set of users into a training program from a BulkEnrollForm."""
    if not bulk_form.is_valid():
        return

    users_to_enroll = set()

    # By department
    dept = bulk_form.cleaned_data.get('department')
    if dept:
        from accounts.models import User
        dept_users = User.objects.filter(
            is_active=True,
            employee_profile__department=dept,
        )
        users_to_enroll.update(dept_users)

    # By individual selection
    selected = bulk_form.cleaned_data.get('employees')
    if selected:
        users_to_enroll.update(selected)

    created = 0
    for user in users_to_enroll:
        _, was_created = TrainingEnrollment.objects.get_or_create(
            training=program,
            employee=user,
        )
        if was_created:
            created += 1

    if created:
        messages.success(request, f'{created} participant(s) enrolled.')
    elif users_to_enroll:
        messages.info(request, 'All selected participants were already enrolled.')


def _auto_complete_enrollments(program):
    """When a training program is marked completed, mark all active enrollments as completed."""
    today = date.today()
    program.enrollments.filter(status='enrolled').update(
        status='completed',
        completion_date=today,
    )
