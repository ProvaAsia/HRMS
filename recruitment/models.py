from django.db import models
from accounts.models import User


class JobPosition(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('on_hold', 'On Hold'),
        ('closed', 'Closed'),
    ]
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    vacancies = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    deadline = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='job_positions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def candidate_count(self):
        return self.candidates.count()


class Candidate(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('interview', 'Interview'),
        ('offered', 'Offered'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ]
    job_position = models.ForeignKey(JobPosition, on_delete=models.CASCADE, related_name='candidates')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Interview(models.Model):
    RESULT_CHOICES = [('pending', 'Pending'), ('pass', 'Pass'), ('fail', 'Fail')]
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='interviews')
    interviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    scheduled_at = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='pending')

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"{self.candidate} — {self.scheduled_at:%Y-%m-%d}"
