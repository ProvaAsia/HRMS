from django.db import models
from accounts.models import User


class TrainingProgram(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    trainer = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=200)
    max_participants = models.PositiveIntegerField(default=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_trainings')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return self.title

    def enrolled_count(self):
        return self.enrollments.filter(status='enrolled').count()

    def spots_left(self):
        return self.max_participants - self.enrolled_count()


class TrainingEnrollment(models.Model):
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    training = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name='enrollments')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    completion_date = models.DateField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('training', 'employee')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.training.title}"
