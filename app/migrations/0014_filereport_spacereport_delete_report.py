# Generated by Django 5.0.1 on 2024-01-10 20:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0013_favorite_time'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FileReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_submitted', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('UR', 'Under Review'), ('RNA', 'No Action Taken'), ('RAT', 'Action Taken')], default='UR', max_length=3)),
                ('file_reported', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.uploadedfile')),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_reports_sent', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='file_reports_reviewed', to=settings.AUTH_USER_MODEL)),
                ('user_reported', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_reports_received', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SpaceReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_submitted', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('UR', 'Under Review'), ('RNA', 'No Action Taken'), ('RAT', 'Action Taken')], default='UR', max_length=3)),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='space_reports_sent', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='space_reports_reviewed', to=settings.AUTH_USER_MODEL)),
                ('space_reported', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.sharespace')),
                ('user_reported', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='space_reports_received', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='Report',
        ),
    ]