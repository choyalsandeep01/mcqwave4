# Generated by Django 4.2.14 on 2024-09-25 21:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mcqs', '0023_bookmark_bkmk_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmark',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
