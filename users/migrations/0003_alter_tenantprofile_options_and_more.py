# Generated by Django 5.1.6 on 2025-02-19 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_serviceproviderprofile_service_provided_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tenantprofile',
            options={'verbose_name': 'Tenant Profile', 'verbose_name_plural': 'Tenant Profiles'},
        ),
        migrations.AddField(
            model_name='tenantprofile',
            name='maintenance_preferences',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='tenantprofile',
            name='move_in_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tenantprofile',
            name='phone_number',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
