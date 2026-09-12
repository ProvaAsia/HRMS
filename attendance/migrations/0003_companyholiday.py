from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_attendancecorrectionrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyHoliday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('name', models.CharField(max_length=200)),
                ('name_en', models.CharField(blank=True, max_length=200)),
            ],
            options={
                'ordering': ['date'],
            },
        ),
    ]
