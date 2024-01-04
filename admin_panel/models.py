from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("account_created", "Account Created"),
        ("login", "Login"),
        ("file_upload", "File Upload"),
        ("report_submitted", "Report Submitted"),
        ("report_change", "Report Change"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"


def create_audit_log_for_new_user(user):
    new_log = AuditLog.objects.create(
        user=user,
        action="account_created",
        message=f"New account {user.username} has been created.",
    )
    new_log.save()

    return new_log


def create_audit_log_for_new_login(user):
    new_log = AuditLog.objects.create(
        user=user, action="login", message=f"New login for the account {user.username}."
    )
    new_log.save()

    return new_log


def create_audit_log_for_space_creation(user, space):
    space_name = space.title
    space_files = len(space.files.all())

    new_log = AuditLog.objects.create(
        user=user,
        action="file_upload",
        message=f"{user.username} has created a new ShareSpace called {space_name} with {space_files} files.",
    )
    new_log.save()

    return new_log


def create_audit_log_for_report_submitted(report):
    new_log = AuditLog.objects.create(
        user=request.reported_by,
        action="report_submitted",
        message=f"{report.reported_by.username} has submitted a report on {report.user_reported.username}.",
    )
    new_log.save()

    return new_log


def create_audit_log_for_report_change(user, report):
    new_log = AuditLog.objects.create(
        user=user,
        action="report_change",
        message=f"{report.reviewed_by.username} has changed the status of Report #{report.id} to {report.get_status_display}.",
    )
    new_log.save()

    return new_log
