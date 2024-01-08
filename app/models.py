from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.timesince import timesince
import string
import random
import os


# Create your models here.
def generate_unique_id():
    # This function generates a unique 8-character ID.
    while True:
        # Creates a random string of 8 letters and digits.
        unique_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        # Checks if the ID is unique across both UploadedFile and ShareSpace models.
        if (
            not UploadedFile.objects.filter(id=unique_id).exists()
            and not ShareSpace.objects.filter(id=unique_id).exists()
        ):
            # If unique, returns the ID.
            return unique_id


class ShareSpace(models.Model):
    # Definition of various visibility choices for a ShareSpace
    class VisibilityChoices(models.TextChoices):
        PUBLIC = "public", "Public"
        PASSWORD_PROTECTED = "password_protected", "Password Protected"
        PRIVATE = "private", "Private"

    # Fields of the ShareSpace model
    id = models.CharField(
        max_length=8, primary_key=True, default=generate_unique_id, editable=False
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=20,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.PRIVATE,
    )
    password = models.CharField(max_length=50, blank=True, null=True)

    def is_accessible_by_user(self, user):
        # Checks if a given user can access this ShareSpace based on its visibility.
        if self.visibility == self.VisibilityChoices.PUBLIC:
            return True
        elif self.visibility == self.VisibilityChoices.PASSWORD_PROTECTED:
            # For password-protected spaces, checks if the user has access.
            if not self.is_owner(user):
                return ShareSpaceAccess.objects.filter(
                    user=user, share_space=self
                ).exists()
        # Private spaces are only accessible by the owner.
        return self.is_owner(user)

    def time_uploaded_from_now(self):
        # Returns a human-readable string representing the time since creation.
        return timesince(self.created_at)

    def is_owner(self, user):
        # Checks if the given user is the owner of the ShareSpace.
        return self.user == user

    def is_favorited(self, user):
        return Favorite.objects.filter(user=user, share_space=self).exists()

    def __str__(self):
        # String representation of the ShareSpace.
        return f"Share Space #{self.id} by {self.user.username}"


def create_shared_space(user, title, description, visibility, password):
    # This function creates a new ShareSpace.
    new_space = ShareSpace.objects.create(
        user=user,
        title=title,
        description=description,
        visibility=visibility,
        password=password,
    )
    new_space.save()  # Explicitly saving the new ShareSpace object.

    return new_space  # Returns the created ShareSpace.


def get_user_spaces(user):
    # Retrieves all ShareSpaces created by a specific user.
    return ShareSpace.objects.filter(user=user)


class ShareSpaceAccess(models.Model):
    # Model to keep track of which users have access to which ShareSpaces.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    share_space = models.ForeignKey(ShareSpace, on_delete=models.CASCADE)
    access_granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures that each user can only have one unique access entry per ShareSpace.
        unique_together = ("user", "share_space")


def check_and_grant_access(user, share_space, password):
    # Checks if the user can access a password-protected ShareSpace.
    if (
        share_space.visibility == ShareSpace.VisibilityChoices.PASSWORD_PROTECTED
        and share_space.password == password
    ):
        # If the password is correct, grant access to the ShareSpace.
        ShareSpaceAccess.objects.get_or_create(user=user, share_space=share_space)

        return True  # Access granted.
    return False  # Access denied if the conditions are not met.


class UploadedFile(models.Model):
    # Fields of the UploadedFile model
    id = models.CharField(
        max_length=8, primary_key=True, default=generate_unique_id, editable=False
    )
    # Link to the ShareSpace this file belongs to, with a reverse relation named 'files'
    share_space = models.ForeignKey(
        ShareSpace, on_delete=models.CASCADE, related_name="files"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # User who uploaded the file
    file = models.FileField(
        upload_to="uploads/"
    )  # The actual file, stored in 'uploads/' directory
    upload_date = models.DateTimeField(auto_now_add=True)  # Date of upload
    file_type = models.CharField(max_length=50, blank=True)  # Type of the file

    def __str__(self):
        return self.title  # String representation of the UploadedFile

    def filename(self):
        # Returns the basename of the file. Useful for displaying just the file name.
        return os.path.basename(self.file.name)

    def is_owner(self, user):
        # Checks if the given user is the owner of this file.
        return self.user == user

    def time_uploaded_from_now(self):
        # Returns a human-readable time since the file was uploaded.
        return timesince(self.upload_date)

    def save(self, *args, **kwargs):
        # Custom save method to automatically set the file type
        if self.file:
            # Extracts and sets the file extension to file_type
            _, file_extension = os.path.splitext(self.file.name)
            self.file_type = file_extension.lower()
        super(UploadedFile, self).save(
            *args, **kwargs
        )  # Calls the superclass save method


def get_user_files(user):
    # Retrieves all files uploaded by a specific user.
    return UploadedFile.objects.filter(user=user)


class Report(models.Model):
    # Nested class for defining report status choices
    class ReportStatus(models.TextChoices):
        UNDER_REVIEW = "UR", "Under Review"
        REVIEWED_NO_ACTION = "RNA", "No Action Taken"
        REVIEWED_ACTION_TAKEN = "RAT", "Action Taken"

    # Fields of the Report model
    reported_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reports_sent"
    )
    user_reported = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reports_received"
    )
    file_reported = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    date_submitted = models.DateTimeField(
        auto_now_add=True
    )  # Date of report submission

    # Status of the report, with predefined choices
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
        # Returns the time since the report was submitted in a human-readable format
        return timesince(self.date_submitted)

    def __str__(self):
        # String representation of a Report instance
        return f"Report #{self.id} on {self.user_reported.username}"


def create_report(reported_by, user_reported, file_reported):
    # Creates a new report
    new_report = Report.objects.create(
        reported_by=reported_by,
        user_reported=user_reported,
        file_reported=file_reported,
    )
    new_report.save()  # Saves the report to the database

    return new_report  # Returns the created report


def get_reports():
    # Retrieves all reports.
    return Report.objects.all()


def review_report(report, reviewed_by, action):
    # Updates a report's status, similar to the above function.
    report.status = action  # Sets the report status.
    report.reviewed_by = reviewed_by  # Sets who reviewed the report.
    report.save()  # Saves the changes to the database.


def get_under_review_reports():
    # Fetches reports that are currently under review.
    under_review_reports = Report.objects.filter(
        status=Report.ReportStatus.UNDER_REVIEW
    )
    return under_review_reports


def get_reviewed_reports():
    # Fetches reports that have been reviewed, either action taken or no action.
    reviewed_reports = Report.objects.filter(
        Q(status=Report.ReportStatus.REVIEWED_ACTION_TAKEN)
        | Q(status=Report.ReportStatus.REVIEWED_NO_ACTION)
    )
    return reviewed_reports


def is_file_taken_down(file):
    # Checks if a file has been taken down based on a report action.
    return Report.objects.filter(
        file_reported=file, status=Report.ReportStatus.REVIEWED_ACTION_TAKEN
    ).exists()


class Favorite(models.Model):
    # Model representing a user's favorite shared spaces.
    share_space = models.ForeignKey(
        ShareSpace, on_delete=models.CASCADE, related_name="favorites"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Favorite for {share_space.title}({share_space.id}) by {user.username}"


def create_favorited_space(share_space, user):
    new_favorite = Favorite.objects.create(user=user, share_space=share_space)
    new_favorite.save()

    return new_favorite


def get_user_favorites(user):
    # Retrieves the favorite shared spaces of a specific user.
    return ShareSpace.objects.filter(favorites__user=user).select_related("user")
