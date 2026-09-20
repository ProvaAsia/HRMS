import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0006_leavetype_max_days'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalLeaveType',
            fields=[
                ('id', models.BigIntegerField(blank=True, db_index=True)),
                ('name', models.CharField(max_length=100)),
                ('name_th', models.CharField(blank=True, max_length=100)),
                ('days_per_year', models.PositiveIntegerField(default=0)),
                ('default_days', models.IntegerField(default=0)),
                ('annual_accrual', models.IntegerField(default=0, help_text='Extra days per year of service')),
                ('max_days', models.IntegerField(default=0, help_text='สูงสุดที่ได้รับ (0 = ไม่จำกัด)')),
                ('requires_advance_days', models.IntegerField(default=0, help_text='Business days in advance required')),
                ('is_paid', models.BooleanField(default=True)),
                ('is_lwp', models.BooleanField(default=False, help_text='ลาไม่รับค่าจ้าง (Leave Without Pay) — ใช้เป็น fallback เมื่อวันลาหมด')),
                ('carry_over', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical leave type',
                'verbose_name_plural': 'historical leave types',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalLeaveBalance',
            fields=[
                ('id', models.BigIntegerField(blank=True, db_index=True)),
                ('year', models.IntegerField(default=2026)),
                ('entitled_days', models.DecimalField(decimal_places=1, default=0, max_digits=5)),
                ('used_days', models.DecimalField(decimal_places=1, default=0, max_digits=5)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('employee', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('leave_type', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='leave.leavetype')),
            ],
            options={
                'verbose_name': 'historical leave balance',
                'verbose_name_plural': 'historical leave balances',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalLeaveRequest',
            fields=[
                ('id', models.BigIntegerField(blank=True, db_index=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('days', models.DecimalField(decimal_places=1, max_digits=4)),
                ('reason', models.TextField(blank=True)),
                ('medical_certificate', models.TextField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(choices=[('pending', 'รอการอนุมัติ'), ('approved', 'อนุมัติแล้ว'), ('rejected', 'ไม่อนุมัติ'), ('cancelled', 'ยกเลิก')], default='pending', max_length=20)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('review_comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('approved_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('leave_type', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='leave.leavetype')),
                ('reviewed_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical leave request',
                'verbose_name_plural': 'historical leave requests',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
