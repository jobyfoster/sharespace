# Generated by Django 5.0.1 on 2024-01-11 14:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_filereport_spacereport_delete_report'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filereport',
            name='file_reported',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='app.uploadedfile'),
        ),
        migrations.AlterField(
            model_name='spacereport',
            name='space_reported',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='app.sharespace'),
        ),
    ]
