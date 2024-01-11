from django.contrib import admin
from .models import UploadedFile, FileReport

# Register your models here.
admin.site.register(UploadedFile)
admin.site.register(FileReport)
