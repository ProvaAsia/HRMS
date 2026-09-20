from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeeprofile',
            name='employee_status',
            field=models.CharField(
                choices=[
                    ('active', 'Active'),
                    ('on_leave', 'On Leave'),
                    ('resigned', 'Resigned'),
                    ('terminated', 'Terminated'),
                    ('retired', 'Retired'),
                ],
                default='active',
                max_length=20,
                verbose_name='Employee status',
            ),
        ),
    ]
