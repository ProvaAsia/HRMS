from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='applicant',
            name='resume',
        ),
        migrations.AddField(
            model_name='applicant',
            name='resume_name',
            field=models.CharField(blank=True, max_length=255, help_text='ชื่อไฟล์ resume'),
        ),
        migrations.AddField(
            model_name='applicant',
            name='resume_sharepoint_url',
            field=models.URLField(blank=True, help_text='SharePoint URL ของ resume — เข้าได้เฉพาะ HR/Admin'),
        ),
    ]
