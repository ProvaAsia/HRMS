import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0003_alter_employeeprofile_employee_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalEmployeeProfile',
            fields=[
                ('id', models.BigIntegerField(blank=True, db_index=True)),
                ('employee_id', models.CharField(db_index=True, max_length=20)),
                ('title_prefix', models.CharField(blank=True, choices=[('mr', 'นาย'), ('mrs', 'นาง'), ('ms', 'นางสาว'), ('dr', 'ดร.'), ('other', 'อื่นๆ')], max_length=10)),
                ('first_name_th', models.CharField(blank=True, max_length=100)),
                ('last_name_th', models.CharField(blank=True, max_length=100)),
                ('first_name_en', models.CharField(blank=True, max_length=100)),
                ('last_name_en', models.CharField(blank=True, max_length=100)),
                ('nickname', models.CharField(blank=True, max_length=50)),
                ('gender', models.CharField(blank=True, choices=[('male', 'ชาย'), ('female', 'หญิง'), ('other', 'ไม่ระบุ')], max_length=10)),
                ('marital_status', models.CharField(blank=True, choices=[('single', 'โสด'), ('married', 'สมรส'), ('divorced', 'หย่าร้าง'), ('widowed', 'หม้าย')], max_length=20)),
                ('national_id', models.CharField(blank=True, max_length=13)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('company_email', models.EmailField(blank=True, max_length=254)),
                ('personal_email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('province', models.CharField(blank=True, max_length=100)),
                ('registered_address', models.TextField(blank=True)),
                ('current_address', models.TextField(blank=True)),
                ('employee_status', models.CharField(choices=[('active', 'ทำงานอยู่'), ('probation', 'ทดลองงาน'), ('resigned', 'ลาออก'), ('terminated', 'ถูกเลิกจ้าง'), ('retired', 'เกษียณ')], default='active', max_length=20, verbose_name='Employee status')),
                ('join_date', models.DateField(blank=True, null=True)),
                ('confirmed_date', models.DateField(blank=True, null=True)),
                ('probation_end_date', models.DateField(blank=True, null=True)),
                ('employment_type', models.CharField(choices=[('full_time', 'Full-time'), ('part_time', 'Part-time'), ('contract', 'Contract'), ('intern', 'Intern'), ('probation', 'Probation')], default='full_time', max_length=20)),
                ('job_title', models.CharField(blank=True, max_length=100)),
                ('job_level', models.CharField(blank=True, max_length=50)),
                ('salary', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('bank_name', models.CharField(blank=True, choices=[('kbank', 'กสิกรไทย (KBank)'), ('scb', 'ไทยพาณิชย์ (SCB)'), ('bbl', 'กรุงเทพ (BBL)'), ('ktb', 'กรุงไทย (KTB)'), ('bay', 'กรุงศรีอยุธยา (BAY)'), ('tmb', 'ทหารไทย (TTB)'), ('gsb', 'ออมสิน (GSB)'), ('baac', 'ธกส. (BAAC)'), ('other', 'อื่นๆ')], max_length=20)),
                ('bank_account', models.CharField(blank=True, max_length=20)),
                ('photo', models.TextField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('cost_center', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='employees.costcenter')),
                ('department', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='employees.department')),
                ('direct_manager', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='employees.employeeprofile')),
                ('division', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='employees.division')),
                ('dotted_line_manager', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='employees.employeeprofile')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('work_location', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='employees.worklocation')),
            ],
            options={
                'verbose_name': 'historical employee profile',
                'verbose_name_plural': 'historical employee profiles',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
