from django.db import migrations, models


def create_lwp(apps, schema_editor):
    LeaveType = apps.get_model('leave', 'LeaveType')
    # Only create if none exists yet
    if not LeaveType.objects.filter(is_lwp=True).exists():
        LeaveType.objects.create(
            name='Leave Without Pay',
            name_th='ลาไม่รับค่าจ้าง',
            default_days=0,
            days_per_year=0,
            annual_accrual=0,
            requires_advance_days=0,
            is_paid=False,
            is_lwp=True,
            carry_over=False,
            description='วันลาที่ไม่มีค่าจ้าง ใช้เมื่อวันลาประเภทอื่นหมดแล้ว',
        )


def reverse_lwp(apps, schema_editor):
    LeaveType = apps.get_model('leave', 'LeaveType')
    LeaveType.objects.filter(is_lwp=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0002_leaverequest_approved_at_leaverequest_approved_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='leavetype',
            name='is_lwp',
            field=models.BooleanField(
                default=False,
                help_text='ลาไม่รับค่าจ้าง (Leave Without Pay) — ใช้เป็น fallback เมื่อวันลาหมด',
            ),
        ),
        migrations.RunPython(create_lwp, reverse_lwp),
    ]
