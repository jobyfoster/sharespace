from django.contrib import admin
from .models import UploadedFile, Report

# Register your models here.
admin.site.register(UploadedFile)
admin.site.register(Report)
