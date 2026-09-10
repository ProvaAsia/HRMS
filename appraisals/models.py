from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User


class AppraisalCycle(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def appraisal_count(self):
        return self.appraisals.count()


class Appraisal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('self_review', 'Self Review'),
        ('manager_review', 'Manager Review'),
        ('completed', 'Completed'),
    ]
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    cycle = models.ForeignKey(AppraisalCycle, on_delete=models.CASCADE, related_name='appraisals')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appraisals')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_appraisals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    self_rating = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    manager_rating = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    self_comments = models.TextField(blank=True)
    manager_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cycle', 'employee')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.cycle.name}"


class Goal(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    appraisal = models.ForeignKey(Appraisal, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    weight = models.PositiveIntegerField(default=0, help_text='Percentage weight (0-100)')
    achievement = models.PositiveIntegerField(default=0, help_text='Achievement % (0-100)',
                                              validators=[MaxValueValidator(100)])

    def __str__(self):
        return self.title
