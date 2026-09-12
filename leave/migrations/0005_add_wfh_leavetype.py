from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0004_leaverequest_medical_cert_maternity'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                INSERT INTO leave_leavetype
                    (name, name_th, days_per_year, default_days, annual_accrual,
                     requires_advance_days, is_paid, is_lwp, carry_over, description)
                SELECT
                    'Work From Home', 'ทำงานจากที่บ้าน', 0, 0, 0,
                    0, true, false, false,
                    'ทำงานจากที่บ้าน (WFH) — ไม่หักวันลา'
                WHERE NOT EXISTS (
                    SELECT 1 FROM leave_leavetype WHERE name = 'Work From Home'
                );
            """,
            reverse_sql="""
                DELETE FROM leave_leavetype WHERE name = 'Work From Home';
            """,
        ),
    ]
