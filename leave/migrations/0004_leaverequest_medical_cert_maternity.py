from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0003_leavetype_is_lwp_add_lwp_record'),
    ]

    operations = [
        # 1. Add medical_certificate field to LeaveRequest
        migrations.AddField(
            model_name='leaverequest',
            name='medical_certificate',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='medical_certs/%Y/%m/',
                help_text='ใบรับรองแพทย์ — บังคับสำหรับลาป่วยเกิน 3 วัน',
            ),
        ),

        # 2. Add Maternity Leave type (ลาคลอด)
        migrations.RunSQL(
            sql="""
                INSERT INTO leave_leavetype
                    (name, name_th, days_per_year, default_days, annual_accrual,
                     requires_advance_days, is_paid, is_lwp, carry_over, description)
                SELECT
                    'Maternity Leave', 'ลาคลอด', 98, 98, 0,
                    0, true, false, false,
                    'ลาคลอดบุตร — สิทธิ์ 98 วัน ตามกฎหมายแรงงานไทย (รวมวันหยุด)'
                WHERE NOT EXISTS (
                    SELECT 1 FROM leave_leavetype WHERE name = 'Maternity Leave'
                );
            """,
            reverse_sql="""
                DELETE FROM leave_leavetype WHERE name = 'Maternity Leave';
            """,
        ),
    ]
