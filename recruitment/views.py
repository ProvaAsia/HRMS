from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobPosition, Candidate, Interview
from .forms import JobPositionForm, CandidateForm, InterviewForm


# ── Job Positions ─────────────────────────────────────────────────────────────

@login_required
def job_list(request):
    jobs = JobPosition.objects.all()
    return render(request, 'recruitment/job_list.html', {'jobs': jobs})


@login_required
def job_create(request):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('job_list')
    form = JobPositionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        job = form.save(commit=False)
        job.created_by = request.user
        job.save()
        messages.success(request, 'Job position created.')
        return redirect('job_detail', pk=job.pk)
    return render(request, 'recruitment/job_form.html', {'form': form, 'title': 'Create Job Position'})


@login_required
def job_detail(request, pk):
    job = get_object_or_404(JobPosition, pk=pk)
    candidates = job.candidates.all()
    return render(request, 'recruitment/job_detail.html', {'job': job, 'candidates': candidates})


@login_required
def job_edit(request, pk):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('job_list')
    job = get_object_or_404(JobPosition, pk=pk)
    form = JobPositionForm(request.POST or None, instance=job)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Job position updated.')
        return redirect('job_detail', pk=job.pk)
    return render(request, 'recruitment/job_form.html', {'form': form, 'title': 'Edit Job Position', 'object': job})


@login_required
def job_delete(request, pk):
    if not request.user.is_super_admin:
        messages.error(request, 'Permission denied.')
        return redirect('job_list')
    job = get_object_or_404(JobPosition, pk=pk)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job position deleted.')
        return redirect('job_list')
    return render(request, 'recruitment/confirm_delete.html', {'object': job, 'back_url': 'job_list'})


# ── Candidates ────────────────────────────────────────────────────────────────

@login_required
def candidate_list(request):
    candidates = Candidate.objects.select_related('job_position').all()
    status_filter = request.GET.get('status')
    if status_filter:
        candidates = candidates.filter(status=status_filter)
    return render(request, 'recruitment/candidate_list.html', {
        'candidates': candidates,
        'status_choices': Candidate.STATUS_CHOICES,
        'status_filter': status_filter,
    })


@login_required
def candidate_create(request):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('candidate_list')
    form = CandidateForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Candidate added.')
        return redirect('candidate_list')
    return render(request, 'recruitment/candidate_form.html', {'form': form, 'title': 'Add Candidate'})


@login_required
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    interviews = candidate.interviews.all()
    interview_form = InterviewForm()
    if request.method == 'POST' and request.user.is_hr_or_admin:
        interview_form = InterviewForm(request.POST)
        if interview_form.is_valid():
            iv = interview_form.save(commit=False)
            iv.candidate = candidate
            iv.save()
            messages.success(request, 'Interview scheduled.')
            return redirect('candidate_detail', pk=pk)
    return render(request, 'recruitment/candidate_detail.html', {
        'candidate': candidate, 'interviews': interviews, 'interview_form': interview_form
    })


@login_required
def candidate_edit(request, pk):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('candidate_list')
    candidate = get_object_or_404(Candidate, pk=pk)
    form = CandidateForm(request.POST or None, request.FILES or None, instance=candidate)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Candidate updated.')
        return redirect('candidate_detail', pk=pk)
    return render(request, 'recruitment/candidate_form.html', {'form': form, 'title': 'Edit Candidate', 'object': candidate})


@login_required
def candidate_delete(request, pk):
    if not request.user.is_hr_or_admin:
        messages.error(request, 'Permission denied.')
        return redirect('candidate_list')
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == 'POST':
        candidate.delete()
        messages.success(request, 'Candidate deleted.')
        return redirect('candidate_list')
    return render(request, 'recruitment/confirm_delete.html', {'object': candidate, 'back_url': 'candidate_list'})
