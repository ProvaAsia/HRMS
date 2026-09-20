from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AppraisalCycle, Appraisal, Goal
from .forms import AppraisalCycleForm, AppraisalForm, SelfReviewForm, ManagerReviewForm, GoalForm


# ── Cycles ────────────────────────────────────────────────────────────────────

@login_required
def cycle_list(request):
    cycles = AppraisalCycle.objects.all()
    # For managers, annotate whether they have appraisals in each cycle
    # (display remains the same; filtering is in cycle_detail)
    return render(request, 'appraisals/cycle_list.html', {
        'cycles': cycles,
        'can_manage': request.user.is_hr_or_admin,
    })


@login_required
def cycle_create(request):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('appraisal_cycle_list')
    form = AppraisalCycleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        c = form.save(commit=False)
        c.created_by = request.user
        c.save()
        messages.success(request, 'Appraisal cycle created.')
        return redirect('appraisal_cycle_detail', pk=c.pk)
    return render(request, 'appraisals/cycle_form.html', {'form': form, 'title': 'Create Appraisal Cycle'})


@login_required
def cycle_detail(request, pk):
    cycle = get_object_or_404(AppraisalCycle, pk=pk)
    appraisals = cycle.appraisals.select_related('employee', 'manager').all()

    user = request.user
    if user.is_hr_or_admin:
        # Admin sees everyone
        pass
    elif user.is_manager:
        # Manager sees only appraisals they are assigned as manager
        appraisals = appraisals.filter(manager=user)
    else:
        # Employee sees only their own appraisal
        appraisals = appraisals.filter(employee=user)

    appraisal_form = AppraisalForm()
    if request.method == 'POST' and user.is_hr_or_admin:
        appraisal_form = AppraisalForm(request.POST)
        if appraisal_form.is_valid():
            a = appraisal_form.save(commit=False)
            a.cycle = cycle
            a.save()
            messages.success(request, 'Appraisal created.')
            return redirect('appraisal_cycle_detail', pk=pk)
    return render(request, 'appraisals/cycle_detail.html', {
        'cycle': cycle,
        'appraisals': appraisals,
        'appraisal_form': appraisal_form,
        'can_manage': user.is_hr_or_admin,
    })


@login_required
def cycle_edit(request, pk):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('appraisal_cycle_list')
    cycle = get_object_or_404(AppraisalCycle, pk=pk)
    form = AppraisalCycleForm(request.POST or None, instance=cycle)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cycle updated.')
        return redirect('appraisal_cycle_detail', pk=pk)
    return render(request, 'appraisals/cycle_form.html', {'form': form, 'title': 'Edit Cycle', 'object': cycle})


# ── Appraisals ────────────────────────────────────────────────────────────────

@login_required
def appraisal_detail(request, pk):
    appraisal = get_object_or_404(Appraisal, pk=pk)
    goals = appraisal.goals.all()
    is_employee = appraisal.employee == request.user
    is_manager = appraisal.manager == request.user or request.user.is_hr_or_admin

    self_form = SelfReviewForm(instance=appraisal) if is_employee else None
    manager_form = ManagerReviewForm(instance=appraisal) if is_manager else None
    goal_form = GoalForm()

    if request.method == 'POST':
        if 'self_submit' in request.POST and is_employee:
            self_form = SelfReviewForm(request.POST, instance=appraisal)
            if self_form.is_valid():
                a = self_form.save(commit=False)
                a.status = 'manager_review'
                a.save()
                messages.success(request, 'Self review submitted.')
                return redirect('appraisal_detail', pk=pk)
        elif 'manager_submit' in request.POST and is_manager:
            manager_form = ManagerReviewForm(request.POST, instance=appraisal)
            if manager_form.is_valid():
                manager_form.save()
                messages.success(request, 'Manager review saved.')
                return redirect('appraisal_detail', pk=pk)
        elif 'goal_submit' in request.POST and (is_employee or is_manager):
            goal_form = GoalForm(request.POST)
            if goal_form.is_valid():
                g = goal_form.save(commit=False)
                g.appraisal = appraisal
                g.save()
                messages.success(request, 'Goal added.')
                return redirect('appraisal_detail', pk=pk)

    return render(request, 'appraisals/appraisal_detail.html', {
        'appraisal': appraisal, 'goals': goals,
        'self_form': self_form, 'manager_form': manager_form,
        'goal_form': goal_form, 'is_employee': is_employee, 'is_manager': is_manager,
    })


@login_required
def goal_update(request, pk):
    goal = get_object_or_404(Goal, pk=pk)
    is_employee = goal.appraisal.employee == request.user
    is_manager = goal.appraisal.manager == request.user or request.user.is_hr_or_admin
    if not (is_employee or is_manager):
        messages.error(request, 'Permission denied.')
        return redirect('appraisal_cycle_list')
    form = GoalForm(request.POST or None, instance=goal)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Goal updated.')
        return redirect('appraisal_detail', pk=goal.appraisal.pk)
    return render(request, 'appraisals/goal_form.html', {'form': form, 'goal': goal})


@login_required
def goal_delete(request, pk):
    goal = get_object_or_404(Goal, pk=pk)
    appraisal_pk = goal.appraisal.pk
    is_employee = goal.appraisal.employee == request.user
    is_manager = goal.appraisal.manager == request.user or request.user.is_hr_or_admin
    if not (is_employee or is_manager):
        messages.error(request, 'Permission denied.')
        return redirect('appraisal_cycle_list')
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted.')
    return redirect('appraisal_detail', pk=appraisal_pk)


@login_required
def my_appraisals(request):
    appraisals = Appraisal.objects.filter(employee=request.user).select_related('cycle')
    return render(request, 'appraisals/my_appraisals.html', {'appraisals': appraisals})
