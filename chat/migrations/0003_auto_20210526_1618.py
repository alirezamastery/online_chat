# Generated by Django 3.2.3 on 2021-05-26 11:48

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0002_rename_text_chatmessage_message'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chatmessage',
            name='user',
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2021, 5, 26, 11, 48, 53, 574825, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='chat',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='chat.chat'),
            preserve_default=False,
        ),
    ]