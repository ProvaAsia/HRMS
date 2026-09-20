from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_simplify_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoginAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(db_index=True, max_length=150)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=300)),
                ('attempt_time', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('success', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-attempt_time'],
            },
        ),
    ]
