from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class AuditLog(models.Model):
    # Choices for different types of audit log actions
    ACTION_CHOICES = [
        # Each action has an internal code and a human-readable description
        ("account_created", "Account Created"),
        ("login", "Login"),
        ("file_upload", "File Upload"),
        ("delete_space", "Delete Space"),
        ("file_report_submitted", "File Report Submitted"),
        ("file_report_change", "File Report Change"),
        ("space_report_submitted", "ShareSpace Report Submitted"),
        ("space_report_change", "Space Report Change"),
        ("invalid_space_password", "Invalid ShareSpace Password Provided"),
    ]

    # Linking each audit log to a specific user
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # The action performed, limited to the choices defined above
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    # A detailed message about the action
    message = models.TextField()
    # Timestamp for when the log was created, auto-set to the current time
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # How the audit log will be displayed as a string, e.g., in the admin panel
        return f"{self.user.username} - {self.action}"


def create_audit_log_for_new_user(user):
    # Creates a new audit log when a user account is created
    new_log = AuditLog.objects.create(
        user=user,
        action="account_created",
        message=f"New account {user.username} has been created.",
    )
    new_log.save()  # Saving the newly created log

    return new_log  # Returning the new log object


def create_audit_log_for_new_login(user):
    # Creates a new audit log for user login
    new_log = AuditLog.objects.create(
        user=user,
        action="login",
        message=f"New login for the account {user.username}({user.id}).",
    )
    new_log.save()  # Saving the newly created log

    return new_log  # Returning the new log object


def create_audit_log_for_space_creation(user, space):
    # Getting details about the space
    space_name = space.title
    space_files = len(space.files.all())

    # Creating a log for a new space creation, specifying the user, action, and a descriptive message
    new_log = AuditLog.objects.create(
        user=user,
        action="file_upload",
        message=f'{user.username} has created a new {space.get_visibility_display()} ShareSpace ({space.id}) called "{space_name}" with {space_files} files in it.',
    )
    new_log.save()  # Saving the log

    return new_log  # Returning the log object


def create_audit_log_for_file_report_submitted(report):
    # Creating a log when a report is submitted
    new_log = AuditLog.objects.create(
        user=report.reported_by,
        action="file_report_submitted",
        message=f"{report.reported_by.username}({report.reported_by.id}) has submitted a file report on {report.user_reported.username}({report.user_reported.id}).",
    )
    new_log.save()  # Saving the log

    return new_log  # Returning the log object


def create_audit_log_for_space_report_submitted(report):
    # Creating a log when a report is submitted
    new_log = AuditLog.objects.create(
        user=report.reported_by,
        action="space_report_submitted",
        message=f"{report.reported_by.username}({report.reported_by.id}) has submitted a ShareSpace report on {report.user_reported.username}({report.user_reported.id}).",
    )
    new_log.save()  # Saving the log

    return new_log  # Returning the log object


def create_audit_log_for_file_report_change(user, report):
    # Creating a log for a change in report status
    new_log = AuditLog.objects.create(
        user=user,
        action="file_report_change",
        message=f"{report.reviewed_by.username}({report.reported_by.id}) has changed the status of File Report #{report.id} to {report.get_status_display()}.",
    )
    new_log.save()  # Saving the log

    return new_log  # Returning the log object


def create_audit_log_for_space_report_change(user, report):
    # Creating a log for a change in report status
    new_log = AuditLog.objects.create(
        user=user,
        action="space_report_change",
        message=f"{report.reviewed_by.username}({report.reported_by.id}) has changed the status of ShareSpace Report #{report.id} to {report.get_status_display()}.",
    )
    new_log.save()  # Saving the log

    return new_log  # Returning the log object


def create_audit_log_for_invalid_space_password(user, space):
    # Creating a log for an invalid password attempt
    new_log = AuditLog.objects.create(
        user=user,
        action="invalid_space_password",
        message=f'{user.username}({user.id}) entered an invalid password for the ShareSpace "{space.title}"({space.id}).',
    )
    new_log.save()  # Saving the log

    return new_log  # Returning the log object


def create_audit_log_for_delete_space(user, space):
    # Creating a log for a space deletion
    new_log = AuditLog.objects.create(
        user=user,
        action="delete_space",
        message=f'{user.username}({user.id}) has deleted the ShareSpace "{space.title}" with ID ({space.id}).',
    )
    new_log.save()  # Saving the log

    return new_log  # Returning the log object
