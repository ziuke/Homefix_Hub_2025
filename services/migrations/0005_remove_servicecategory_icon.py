# Generated by Django 5.1.6 on 2025-02-20 09:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0004_directservicerequest'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servicecategory',
            name='icon',
        ),
    ]
