from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TrainingProgram, TrainingEnrollment
from .forms import TrainingProgramForm, EnrollmentForm


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
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('training_list')
    form = TrainingProgramForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        t = form.save(commit=False)
        t.created_by = request.user
        t.save()
        messages.success(request, 'Training program created.')
        return redirect('training_detail', pk=t.pk)
    return render(request, 'training/program_form.html', {'form': form, 'title': 'Create Training Program'})


@login_required
def training_detail(request, pk):
    program = get_object_or_404(TrainingProgram, pk=pk)
    enrollments = program.enrollments.select_related('employee').all()
    enroll_form = EnrollmentForm()

    # Check if current user is already enrolled
    user_enrolled = enrollments.filter(employee=request.user).exists()

    if request.method == 'POST':
        if 'self_enroll' in request.POST:
            if not user_enrolled:
                TrainingEnrollment.objects.create(training=program, employee=request.user)
                messages.success(request, 'You have enrolled successfully.')
            return redirect('training_detail', pk=pk)
        elif request.user.is_hr_or_admin:
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
        'user_enrolled': user_enrolled,
    })


@login_required
def training_edit(request, pk):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('training_list')
    program = get_object_or_404(TrainingProgram, pk=pk)
    form = TrainingProgramForm(request.POST or None, instance=program)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Training updated.')
        return redirect('training_detail', pk=pk)
    return render(request, 'training/program_form.html', {'form': form, 'title': 'Edit Training', 'object': program})


@login_required
def training_delete(request, pk):
    if not request.user.is_super_admin:
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
    if not request.user.is_hr_or_admin:
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
    if not request.user.is_hr_or_admin:
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
