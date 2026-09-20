from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0002_employeeprofile_employee_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_type', models.CharField(
                    choices=[
                        ('contract', 'สัญญาจ้าง / Employment Contract'),
                        ('id_card', 'บัตรประชาชน / National ID'),
                        ('transcript', 'ใบจบการศึกษา / Transcript'),
                        ('certificate', 'ประกาศนียบัตร / Certificate'),
                        ('medical', 'ผลตรวจสุขภาพ / Medical Certificate'),
                        ('visa', 'วีซ่า / Visa'),
                        ('passport', 'หนังสือเดินทาง / Passport'),
                        ('other', 'อื่นๆ / Other'),
                    ],
                    default='other',
                    max_length=30,
                )),
                ('title', models.CharField(max_length=200)),
                ('file', models.FileField(blank=True, null=True, upload_to='employee_documents/')),
                ('issue_date', models.DateField(blank=True, null=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('note', models.TextField(blank=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='documents',
                    to='employees.employeeprofile',
                )),
            ],
        ),
    ]
