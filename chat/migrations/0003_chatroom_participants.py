# Generated by Django 5.1.6 on 2025-02-14 05:53

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_notification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='participants',
            field=models.ManyToManyField(related_name='chat_rooms', to=settings.AUTH_USER_MODEL),
        ),
    ]
