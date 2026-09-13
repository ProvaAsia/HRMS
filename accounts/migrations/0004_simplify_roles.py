from django.db import migrations, models


def migrate_roles_forward(apps, schema_editor):
    """
    เปลี่ยน role เก่า → role ใหม่
      super_admin  →  admin
      hr_manager   →  employee
    """
    User = apps.get_model('accounts', 'User')
    User.objects.filter(role='super_admin').update(role='admin')
    User.objects.filter(role='hr_manager').update(role='employee')


def migrate_roles_backward(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(role='admin').update(role='super_admin')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_demote_director_from_super_admin'),
    ]

    operations = [
        # แปลง data ก่อน (ยังใช้ field เดิม max_length=20 ได้)
        migrations.RunPython(migrate_roles_forward, migrate_roles_backward),

        # อัปเดต choices ใน schema
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'),
                    ('manager', 'Manager'),
                    ('employee', 'Employee'),
                ],
                default='employee',
                max_length=20,
            ),
        ),
    ]
