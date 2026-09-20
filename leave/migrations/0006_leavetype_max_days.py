from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0005_add_wfh_leavetype'),
    ]

    operations = [
        migrations.AddField(
            model_name='leavetype',
            name='max_days',
            field=models.IntegerField(default=0, help_text='สูงสุดที่ได้รับ (0 = ไม่จำกัด)'),
        ),
    ]
