from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0002_employee_360_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employeeprofile',
            name='employee_status',
            field=models.CharField(
                choices=[
                    ('active', 'ทำงานอยู่'),
                    ('probation', 'ทดลองงาน'),
                    ('resigned', 'ลาออก'),
                    ('terminated', 'ถูกเลิกจ้าง'),
                    ('retired', 'เกษียณ'),
                ],
                default='active',
                max_length=20,
                verbose_name='Employee status',
            ),
        ),
    ]
