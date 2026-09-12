from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceCorrectionRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('requested_clock_in', models.TimeField(blank=True, null=True)),
                ('requested_clock_out', models.TimeField(blank=True, null=True)),
                ('requested_status', models.CharField(
                    blank=True, max_length=20,
                    choices=[
                        ('present', 'Present'), ('late', 'Late'), ('half_day', 'Half Day'),
                        ('absent', 'Absent'), ('wfh', 'Work from Home'), ('leave', 'On Leave'),
                    ]
                )),
                ('reason', models.TextField()),
                ('status', models.CharField(
                    default='pending', max_length=20,
                    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]
                )),
                ('review_note', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('attendance_record', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='correction_requests',
                    to='attendance.attendancerecord',
                )),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='correction_requests',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_corrections',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
