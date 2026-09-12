from django.db import migrations


class Migration(migrations.Migration):
    """
    เปลี่ยน role ของ Wichai Pongsuwat จาก super_admin → manager
    (Director ไม่ควรมีสิทธิ์ HR/Admin ในระบบ)
    """

    dependencies = [
        ('accounts', '0002_add_manager_role'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                UPDATE accounts_user
                SET role = 'manager'
                WHERE role = 'super_admin'
                  AND (username = 'wichai' OR first_name ILIKE 'Wichai')
                  AND last_name ILIKE 'Pongsuwat';
            """,
            reverse_sql="""
                UPDATE accounts_user
                SET role = 'super_admin'
                WHERE (username = 'wichai' OR first_name ILIKE 'Wichai')
                  AND last_name ILIKE 'Pongsuwat';
            """,
        ),
    ]
