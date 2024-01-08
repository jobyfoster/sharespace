from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.contrib import messages
from .forms import FileUploadForm, ShareSpaceAccessForm
from django.conf import settings
from .models import (
    ShareSpace,
    UploadedFile,
    Report,
    ShareSpaceAccess,
    Favorite,
    get_user_spaces,
    create_report,
    is_file_taken_down,
    create_shared_space,
    check_and_grant_access,
    get_user_favorites,
    create_favorited_space,
)

from admin_panel.models import (
    AuditLog,
    create_audit_log_for_report_change,
    create_audit_log_for_space_creation,
    create_audit_log_for_report_submitted,
    create_audit_log_for_invalid_space_password,
    create_audit_log_for_delete_space,
)
from django.db.models import Case, When
import os


def home(request):
    return render(request, "app/home.html")


@login_required  # This decorator ensures only logged-in users can access this view.
def upload(request):
    if request.method == "POST":
        # When the form is submitted (POST request), process the form data.
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract data from the valid form.
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            files = form.cleaned_data["file_field"]
            visibility = form.cleaned_data["visibility"]
            password = form.cleaned_data["password"]

            # Create a new shared space with the provided data.
            share_space = create_shared_space(
                user=request.user,
                title=title,
                description=description,
                visibility=visibility,
                password=password,
            )

            # For each file in the submission, create an UploadedFile instance.
            for file in files:
                UploadedFile.objects.create(
                    share_space=share_space,
                    user=request.user,
                    file=file,
                )

            # Display a success message to the user.
            messages.success(request, "Share space successfully created!")
            # Log the creation of the new shared space.
            create_audit_log_for_space_creation(request.user, share_space)
            # Redirect the user to view the newly created shared space.
            return redirect("view_share_space", space_id=share_space.id)
    else:
        # If it's not a POST request, display an empty form.
        form = FileUploadForm()

    # Render the page with the form.
    return render(request, "app/upload_file.html", {"form": form})


@login_required
def view_share_space(request, space_id):
    # Retrieves the ShareSpace with the given ID or shows a 404 error if not found.
    share_space = get_object_or_404(ShareSpace, id=space_id)

    # Check if the current user has access to the ShareSpace.
    if not share_space.is_accessible_by_user(request.user):
        # Redirects to a password input page for password-protected spaces.
        if share_space.visibility == ShareSpace.VisibilityChoices.PASSWORD_PROTECTED:
            return redirect("space_password", space_id=space_id)
        # Shows an error message and redirects to the home page for private spaces.
        elif share_space.visibility == ShareSpace.VisibilityChoices.PRIVATE:
            messages.error(
                request, "This is a private ShareSpace that you do not have access to!"
            )
            return redirect("home")

    # Retrieves all files associated with this ShareSpace.
    share_space_files = share_space.files.all()
    # Checks if the user owns this ShareSpace
    is_owner = share_space.is_owner(user=request.user)
    # Checks if the user owns this ShareSpace
    is_favorited = share_space.is_favorited(user=request.user)

    # Renders the ShareSpace page with its details and files.
    return render(
        request,
        "app/share_space.html",
        context={
            "share_space": share_space,
            "files": share_space_files,
            "is_owner": is_owner,
            "is_favorited": is_favorited,
        },
    )


@login_required
def enter_space_password(request, space_id):
    # Retrieves the specific ShareSpace or shows a 404 error if not found.
    share_space = get_object_or_404(ShareSpace, id=space_id)
    form = ShareSpaceAccessForm()  # Initializes the access form

    # Checks if the user already has access to the share space.
    if share_space.is_accessible_by_user(request.user):
        messages.success(request, "You already have access to this space")
        return redirect("view_share_space", space_id=space_id)

    # Processes the form on POST request.
    if request.method == "POST":
        form = ShareSpaceAccessForm(request.POST)
        if form.is_valid():
            # Checks the provided password.
            password = form.cleaned_data["password"]
            if check_and_grant_access(
                user=request.user, share_space=share_space, password=password
            ):
                # Redirects to the share space view if the password is correct.
                return redirect("view_share_space", space_id=space_id)
            else:
                # Logs an invalid password attempt and shows an error message.
                create_audit_log_for_invalid_space_password(
                    user=request.user, space=share_space
                )
                messages.error(request, "Incorrect password")

    # Renders the password entry form for the share space.
    return render(
        request, "app/enter_space_password.html", {"form": form, "space": share_space}
    )


@login_required
def download_file_view(request, file_id):
    # Retrieves the UploadedFile instance or shows a 404 error if not found.
    file_instance = get_object_or_404(UploadedFile, id=file_id)

    # Checks if the file actually exists in the database.
    if not file_instance.file:
        raise Http404(
            "File does not exist"
        )  # Raises a 404 error if the file doesn't exist.

    # Verifies if the user has access to the ShareSpace containing the file.
    if not file_instance.share_space.is_accessible_by_user(user=request.user):
        # Displays an error message and redirects to the home page if the user lacks access.
        messages.error(
            request, "You do not have access to the ShareSpace this file is in."
        )
        return redirect("home")

    # Checks if the file has been taken down due to a report.
    if is_file_taken_down(file_instance):
        # Fetches the report associated with the file.
        report = Report.objects.get(file_reported=file_instance)
        # Renders a page indicating the file has been taken down, displaying the report details.
        return render(request, "app/file_taken_down.html", {"report": report})

    preview_templates = {
        ".jpg": "app/partials/preview_image.html",
        ".jpeg": "app/partials/preview_image.html",
        ".png": "app/partials/preview_image.html",
        ".webp": "app/partials/preview_image.html",
        ".gif": "app/partials/preview_image.html",
        ".pdf": "app/partials/preview_pdf.html",
        ".mp3": "app/partials/preview_audio.html",
        ".wav": "app/partials/preview_audio.html",
        ".mp4": "app/partials/preview_video.html",
        ".avi": "app/partials/preview_video.html",
        ".txt": "app/partials/preview_text.html",
        ".csv": "app/partials/preview_text.html",
    }

    preview_template = preview_templates.get(file_instance.file_type, None)

    # Pass the preview template name to the context
    return render(
        request,
        "app/download_file.html",
        {
            "file": file_instance,
            "preview_template": preview_template,
            "previewable_types": preview_templates.keys(),
        },
    )


@login_required
def user_spaces(request):
    # Retrieve all shared spaces created by the user.
    users_spaces = get_user_spaces(user=request.user)

    # Retrieve all shared spaces favorited by the user.
    users_favorites = get_user_favorites(user=request.user)

    # Combine and sort the shared spaces and favorited spaces.
    # We use a queryset union and sort by 'created_at'.
    # 'distinct' is used to avoid duplicate entries.
    combined_spaces = (users_spaces | users_favorites).distinct().order_by("created_at")

    return render(request, "app/user_files.html", {"spaces": combined_spaces})


@login_required
def report_file(request, file_id):
    # The user who is making the report.
    reported_by = request.user
    # Retrieves the file to be reported or shows a 404 error if not found.
    reported_file = get_object_or_404(UploadedFile, id=file_id)
    # The owner of the file being reported.
    user_reported = reported_file.user

    # Prevents users from reporting their own files.
    if reported_by == user_reported:
        messages.error(request, "You cannot report a file that you own.")
        # Redirects back to the file download page.
        return redirect("download", file_id=file_id)

    # Creates a new report.
    new_report = create_report(
        reported_by=reported_by,
        user_reported=user_reported,
        file_reported=reported_file,
    )

    # Shows a success message upon submitting the report.
    messages.success(request, "Report successfully submitted!")
    # Creates an audit log for the submission of this report.
    create_audit_log_for_report_submitted(new_report)
    # Redirects back to the file download page.
    return redirect("download", file_id=file_id)


@login_required
def delete_file(request, file_id):
    # The user who is making the request to delete the file.
    user = request.user
    # Retrieves the file to be deleted or shows a 404 error if not found.
    file = get_object_or_404(UploadedFile, id=file_id)

    # Checks if the user is the owner of the file.
    is_owner = file.is_owner(user)

    # If the user is not the owner of the file, they are prevented from deleting it.
    if not is_owner:
        messages.error(request, "You do not own this file!")
        # Redirects to the home page.
        return redirect("home")

    # Deletes the file from the database.
    file.delete()

    # Shows a success message after the file is deleted.
    messages.success(request, "File deleted successfully!")
    # Redirects to the home page.
    return redirect("home")


@login_required
def delete_space(request, space_id):
    # The current user who wants to delete the space.
    user = request.user
    # Retrieves the specific ShareSpace or shows a 404 error if not found.
    space = get_object_or_404(ShareSpace, id=space_id)

    # Checks if the current user is the owner of the space.
    is_owner = space.is_owner(user)

    # If the user is not the owner, they're prevented from deleting the space.
    if not is_owner:
        messages.error(request, "You do not own this space!")
        # Redirects back to the view page of the space.
        return redirect("view_share_space", space_id=space_id)

    if request.POST:
        # Deletes the space if the user is the owner.
        space.delete()

        # Shows a success message indicating the space has been deleted.
        messages.success(request, "Space deleted successfully!")
        # Redirects the user to a page showing their spaces (presumably 'user_spaces').
        return redirect("user_spaces")

    return render(request, "app/confirm_space_delete.html", {"share_space": space})


@login_required
def favorite_space(request, space_id):
    # Retrieves the specified ShareSpace or shows a 404 error if not found.
    share_space = get_object_or_404(ShareSpace, id=space_id)

    # Checks if the user has access to the ShareSpace.
    if share_space.is_accessible_by_user(user=request.user):
        # If the user has access, the space is added to their favorites.
        create_favorited_space(user=request.user, share_space=share_space)
        # Displays a success message.
        messages.success(request, "Successfully favorited!")
        # Redirects back to the ShareSpace view.
        return redirect("view_share_space", space_id=space_id)
    else:
        # If the user doesn't have access, an error message is shown.
        messages.error(
            request, "You cannot favorite a ShareSpace unless you have access to it!"
        )
        # Redirects to the home page.
        return redirect("home")


@login_required
def unfavorite_space(request, space_id):
    # Retrieves the specified ShareSpace or shows a 404 error if not found.
    share_space = get_object_or_404(ShareSpace, id=space_id)

    # Checks if the ShareSpace is already favorited by the user.
    if share_space.is_favorited(user=request.user):
        # Retrieves the user's favorite instance and deletes it.
        user_favorite = Favorite.objects.get(user=request.user, share_space=share_space)
        user_favorite.delete()

        # Shows a success message upon successful unfavoriting.
        messages.success(request, "Successfully unfavorited!")
        # Redirects back to the ShareSpace view.
        return redirect("view_share_space", space_id=space_id)
    else:
        # If the space is not favorited, an error message is displayed.
        messages.error(
            request, "You cannot unfavorite a ShareSpace you do not have favorited!"
        )
        # Redirects to the home page.
        return redirect("home")
