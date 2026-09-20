from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0004_historicalemployeeprofile'),
    ]

    operations = [
        # ── EmployeeProfile: photo ImageField → photo_url URLField ──
        migrations.RemoveField(
            model_name='employeeprofile',
            name='photo',
        ),
        migrations.RemoveField(
            model_name='historicalemployeeprofile',
            name='photo',
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='photo_url',
            field=models.URLField(blank=True, help_text='URL รูปภาพพนักงาน (SharePoint public link หรือ URL อื่น)'),
        ),
        migrations.AddField(
            model_name='historicalemployeeprofile',
            name='photo_url',
            field=models.URLField(blank=True, help_text='URL รูปภาพพนักงาน (SharePoint public link หรือ URL อื่น)'),
        ),
        # ── EmployeeDocument: file FileField → file_sharepoint_url URLField ──
        migrations.RemoveField(
            model_name='employeedocument',
            name='file',
        ),
        migrations.AddField(
            model_name='employeedocument',
            name='file_sharepoint_url',
            field=models.URLField(blank=True, help_text='SharePoint URL ของไฟล์เอกสาร — เข้าได้เฉพาะ HR/Admin'),
        ),
    ]
