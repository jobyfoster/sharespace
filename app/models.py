from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.timesince import timesince
import string
import random
import os

# Create your models here.


def generate_unique_id():
    while True:
        unique_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        if (
            not UploadedFile.objects.filter(id=unique_id).exists()
            or not ShareSpace.objects.filter(id=unique_id).exists()
        ):
            return unique_id


class ShareSpace(models.Model):
    id = models.CharField(
        max_length=8, primary_key=True, default=generate_unique_id, editable=False
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=64)
    description = models.TextField(blank=True)

    def time_uploaded_from_now(self):
        return timesince(self.created_at)

    def is_owner(self, user):
        return self.user == user

    def __str__(self):
        return f"Share Space #{self.id} by {self.user.username}"


def create_shared_space(user, title, description):
    new_space = ShareSpace.objects.create(
        user=user, title=title, description=description
    )
    new_space.save()

    return new_space


def get_user_spaces(user):
    return ShareSpace.objects.filter(user=user)


class UploadedFile(models.Model):
    id = models.CharField(
        max_length=8, primary_key=True, default=generate_unique_id, editable=False
    )
    share_space = models.ForeignKey(
        ShareSpace, on_delete=models.CASCADE, related_name="files"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="uploads/")
    upload_date = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.title

    def filename(self):
        return os.path.basename(self.file.name)

    def is_owner(self, user):
        return self.user == user

    def time_uploaded_from_now(self):
        return timesince(self.upload_date)

    def save(self, *args, **kwargs):
        if self.file:
            _, file_extension = os.path.splitext(self.file.name)
            self.file_type = file_extension.lower()
        super(UploadedFile, self).save(*args, **kwargs)


def get_user_files(user):
    return UploadedFile.objects.filter(user=user)


class Report(models.Model):
    class ReportStatus(models.TextChoices):
        UNDER_REVIEW = "UR", "Under Review"
        REVIEWED_NO_ACTION = "RNA", "No Action Taken"
        REVIEWED_ACTION_TAKEN = "RAT", "Action Taken"

    reported_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reports_sent"
    )
    user_reported = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reports_received"
    )
    file_reported = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    date_submitted = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=3,
        choices=ReportStatus.choices,
        default=ReportStatus.UNDER_REVIEW,
        editable=True,
    )

    reviewed_by = models.ForeignKey(
        User, related_name="reports_reviewed", null=True, on_delete=models.CASCADE
    )

    def time_since_submission(self):
        return timesince(self.date_submitted)

    def __str__(self):
        return f"Report #{self.id} on {self.user_reported.username}"


def create_report(reported_by, user_reported, file_reported):
    new_report = Report.objects.create(
        reported_by=reported_by,
        user_reported=user_reported,
        file_reported=file_reported,
    )
    new_report.save()

    return new_report


def get_reports():
    return UploadedFile.objects.all()


def review_report_no_action(report, reviewed_by, action):
    report.status = action
    report.reviewed_by = reviewed_by
    report.save()


def review_report(report, reviewed_by, action):
    report.status = action
    report.reviewed_by = reviewed_by
    report.save()


def get_under_review_reports():
    under_review_reports = Report.objects.filter(
        status=Report.ReportStatus.UNDER_REVIEW
    )

    return under_review_reports


def get_reviewed_reports():
    reviewed_reports = Report.objects.filter(
        Q(status=Report.ReportStatus.REVIEWED_ACTION_TAKEN)
        | Q(status=Report.ReportStatus.REVIEWED_NO_ACTION)
    )

    return reviewed_reports


def is_file_taken_down(file):
    return Report.objects.filter(
        file_reported=file, status=Report.ReportStatus.REVIEWED_ACTION_TAKEN
    ).exists()
