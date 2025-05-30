# Generated by Django 5.1.6 on 2025-02-20 09:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0005_remove_servicecategory_icon'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servicerequest',
            name='category',
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='service_requests', to='services.servicecategory'),
        ),
    ]
