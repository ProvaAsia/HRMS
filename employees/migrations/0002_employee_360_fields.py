from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        # Add new fields to EmployeeProfile
        migrations.AddField(
            model_name='employeeprofile',
            name='title_prefix',
            field=models.CharField(
                blank=True, max_length=10,
                choices=[('mr', 'นาย'), ('mrs', 'นาง'), ('ms', 'นางสาว'), ('dr', 'ดร.'), ('other', 'อื่นๆ')]
            ),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='nickname',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='gender',
            field=models.CharField(
                blank=True, max_length=10,
                choices=[('male', 'ชาย'), ('female', 'หญิง'), ('other', 'ไม่ระบุ')]
            ),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='marital_status',
            field=models.CharField(
                blank=True, max_length=20,
                choices=[('single', 'โสด'), ('married', 'สมรส'), ('divorced', 'หย่าร้าง'), ('widowed', 'หม้าย')]
            ),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='province',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='employee_status',
            field=models.CharField(
                default='active', max_length=20,
                choices=[('active', 'ทำงานอยู่'), ('probation', 'ทดลองงาน'),
                         ('resigned', 'ลาออก'), ('terminated', 'ถูกเลิกจ้าง'), ('retired', 'เกษียณ')]
            ),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='confirmed_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='job_level',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='salary',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='bank_name',
            field=models.CharField(
                blank=True, max_length=20,
                choices=[('kbank', 'กสิกรไทย (KBank)'), ('scb', 'ไทยพาณิชย์ (SCB)'),
                         ('bbl', 'กรุงเทพ (BBL)'), ('ktb', 'กรุงไทย (KTB)'),
                         ('bay', 'กรุงศรีอยุธยา (BAY)'), ('tmb', 'ทหารไทย (TTB)'),
                         ('gsb', 'ออมสิน (GSB)'), ('baac', 'ธกส. (BAAC)'), ('other', 'อื่นๆ')]
            ),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='bank_account',
            field=models.CharField(blank=True, max_length=20),
        ),
        # Create EmployeeDocument model
        migrations.CreateModel(
            name='EmployeeDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_type', models.CharField(
                    max_length=30,
                    choices=[('id_card', 'บัตรประชาชน'), ('passport', 'หนังสือเดินทาง'),
                             ('driver_license', 'ใบอนุญาตขับขี่'), ('medical_cert', 'ใบรับรองแพทย์'),
                             ('education_cert', 'วุฒิการศึกษา'), ('transcript', 'ผลการเรียน'),
                             ('work_permit', 'ใบอนุญาตทำงาน'), ('other', 'อื่นๆ')]
                )),
                ('doc_name', models.CharField(blank=True, max_length=200)),
                ('doc_number', models.CharField(blank=True, max_length=50)),
                ('issue_date', models.DateField(blank=True, null=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(
                    default='active', max_length=20,
                    choices=[('active', 'ปกติ'), ('expired', 'หมดอายุ'), ('pending', 'รอดำเนินการ')]
                )),
                ('file', models.FileField(blank=True, null=True, upload_to='employee_documents/%Y/')),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='employee_documents',
                    to='employees.employeeprofile'
                )),
            ],
            options={
                'ordering': ['-issue_date'],
            },
        ),
    ]
