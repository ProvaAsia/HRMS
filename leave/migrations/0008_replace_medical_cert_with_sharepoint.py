from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0007_historicalleavetype_historicalleaverequest_and_more'),
    ]

    operations = [
        # Remove old FileField
        migrations.RemoveField(
            model_name='leaverequest',
            name='medical_certificate',
        ),
        migrations.RemoveField(
            model_name='historicalleaverequest',
            name='medical_certificate',
        ),
        # Add new fields
        migrations.AddField(
            model_name='leaverequest',
            name='medical_cert_name',
            field=models.CharField(blank=True, max_length=255, help_text='ชื่อไฟล์ใบรับรองแพทย์ (แสดงให้พนักงานเห็น)'),
        ),
        migrations.AddField(
            model_name='leaverequest',
            name='medical_cert_sharepoint_url',
            field=models.URLField(blank=True, help_text='SharePoint URL — เข้าได้เฉพาะ HR/Admin'),
        ),
        migrations.AddField(
            model_name='historicalleaverequest',
            name='medical_cert_name',
            field=models.CharField(blank=True, max_length=255, help_text='ชื่อไฟล์ใบรับรองแพทย์ (แสดงให้พนักงานเห็น)'),
        ),
        migrations.AddField(
            model_name='historicalleaverequest',
            name='medical_cert_sharepoint_url',
            field=models.URLField(blank=True, help_text='SharePoint URL — เข้าได้เฉพาะ HR/Admin'),
        ),
    ]
