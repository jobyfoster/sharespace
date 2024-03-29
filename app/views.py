from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from .forms import (
    FileUploadForm,
    ShareSpaceAccessForm,
    PasswordChangingForm,
    UsernameChangingForm,
    EditShareSpaceForm,
)
from django.conf import settings
from .models import (
    ShareSpace,
    UploadedFile,
    FileReport,
    SpaceReport,
    ShareSpaceAccess,
    Favorite,
    get_user_spaces,
    create_file_report,
    create_space_report,
    is_file_taken_down,
    create_shared_space,
    check_and_grant_access,
    get_user_favorites,
    create_favorited_space,
    is_space_taken_down,
)

from admin_panel.models import (
    AuditLog,
    create_audit_log_for_file_report_change,
    create_audit_log_for_space_creation,
    create_audit_log_for_file_report_submitted,
    create_audit_log_for_space_report_submitted,
    create_audit_log_for_invalid_space_password,
    create_audit_log_for_delete_space,
)
from django.db.models import Case, When
from django.core.paginator import Paginator
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
    share_space = get_object_or_404(ShareSpace, id=space_id)

    if is_space_taken_down(share_space):
        report = SpaceReport.objects.get(space_reported=share_space)
        return render(request, "app/space_taken_down.html", {"report": report})

    if not share_space.is_accessible_by_user(request.user):
        if share_space.visibility == ShareSpace.VisibilityChoices.PASSWORD_PROTECTED:
            return redirect("space_password", space_id=space_id)
        elif share_space.visibility == ShareSpace.VisibilityChoices.PRIVATE:
            messages.error(request, "This is a private ShareSpace that you do not have access to!")
            return redirect("home")

    share_space_files = share_space.files.all()

    # Implementing search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        # Assuming 'file' field contains the filename or filepath
        share_space_files = share_space_files.filter(file__icontains=search_query)

    is_owner = share_space.is_owner(user=request.user)
    is_favorited = share_space.is_favorited(user=request.user)

    # Pagination
    paginator = Paginator(share_space_files, 10)  # Adjust the number per page as needed
    page_number = request.GET.get("page")
    files = paginator.get_page(page_number)

    return render(
        request,
        "app/share_space.html",
        {
            "share_space": share_space,
            "files": files,
            "is_owner": is_owner,
            "is_favorited": is_favorited,
        }
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
            request,
            "You do not have access to the ShareSpace this file is in, please enter the password.",
        )
        return redirect("view_share_space", space_id=file_instance.share_space.id)

    # Checks if the file has been taken down due to a report.
    if is_file_taken_down(file_instance):
        # Fetches the report associated with the file.
        report = FileReport.objects.get(file_reported=file_instance)
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

    file_content = None
    if preview_template == preview_templates[".txt"]:
        f = open(file_instance.file.path, "r", encoding="utf8")
        file_content = f.read()
        f.close()

    is_owner = file_instance.is_owner(user=request.user)
    # Pass the preview template name to the context
    return render(
        request,
        "app/download_file.html",
        {
            "file": file_instance,
            "file_content": file_content,
            "is_owner": is_owner,
            "preview_template": preview_template,
            "previewable_types": preview_templates.keys(),
        },
    )


@login_required
def user_spaces(request):
    search_query = request.GET.get('search', '')  # Get the search term from the request

    # Retrieve all shared spaces created or favorited by the user
    users_spaces = get_user_spaces(user=request.user)
    users_favorites = get_user_favorites(user=request.user)
    combined_spaces = (users_spaces | users_favorites).distinct().order_by("-created_at")

    # If there is a search term, filter the combined spaces
    if search_query:
        combined_spaces = combined_spaces.filter(title__icontains=search_query)

    paginator = Paginator(combined_spaces, 10)
    page_number = request.GET.get("page")
    spaces = paginator.get_page(page_number)

    return render(request, "app/user_files.html", {"spaces": spaces})



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

    if reported_file.has_user_reported(reported_by):
        messages.error(request, "You have already reported this file before!")
        # Redirects back to the ShareSpace page.
        return redirect("download", file_id=file_id)

    if len(reported_file.reports.all()) > 0:
        messages.error(
            request,
            "Somebody has already reported this file! An admin will review it soon!",
        )
        # Redirects back to the ShareSpace page.
        return redirect("download", file_id=file_id)

    # Creates a new file report.
    new_report = create_file_report(
        reported_by=reported_by,
        user_reported=user_reported,
        file_reported=reported_file,
    )

    # Shows a success message upon submitting the report.
    messages.success(
        request,
        "Successfully reported this file! An admin will review your report soon!",
    )
    # Creates an audit log for the submission of this report.
    create_audit_log_for_file_report_submitted(new_report)
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
def report_space(request, space_id):
    reported_by = request.user
    space_reported = get_object_or_404(ShareSpace, id=space_id)
    user_reported = space_reported.user

    # Prevents users from reporting their own ShareSpaces.
    if reported_by == user_reported:
        messages.error(request, "You cannot report a ShareSpace that you own.")
        # Redirects back to the ShareSpace page.
        return redirect("view_share_space", space_id=space_id)

    if space_reported.has_user_reported(reported_by):
        messages.error(request, "You have already reported this ShareSpace before!")
        # Redirects back to the ShareSpace page.
        return redirect("view_share_space", space_id=space_id)

    if len(space_reported.reports.all()) > 0:
        messages.error(
            request,
            "Somebody has already reported this ShareSpace! An admin will review it soon!",
        )
        # Redirects back to the ShareSpace page.
        return redirect("view_share_space", space_id=space_id)

    new_report = create_space_report(
        reported_by=reported_by,
        user_reported=user_reported,
        space_reported=space_reported,
    )

    messages.success(
        request,
        "Successfully reported this ShareSpace! An admin will review your report soon!",
    )
    # Creates an audit log for the submission of this report.
    create_audit_log_for_space_report_submitted(new_report)
    # Redirects back to the ShareSpace page.
    return redirect("view_share_space", space_id=space_id)


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


@login_required
def settings_view(request):  # Defining a view function named 'settings_view'.
    if request.method == "POST":  # Checking if the request is a POST request.
        if (
            "change_password" in request.POST
        ):  # Check if the 'change_password' action was triggered.
            # Creating a PasswordChangingForm with the current user and POST data.
            password_form = PasswordChangingForm(request.user, request.POST)
            if password_form.is_valid():  # Validating the form.
                password_form.save()  # If valid, save the new password.
                # Display a success message to the user.
                messages.success(request, "Your password has been updated!")
        else:
            # If it's not a password change request, initialize the form without POST data.
            password_form = PasswordChangingForm(request.user)

        if (
            "change_username" in request.POST
        ):  # Check if the 'change_username' action was triggered.
            # Creating a UsernameChangingForm with POST data and the current user instance.
            username_form = UsernameChangingForm(request.POST, instance=request.user)
            if username_form.is_valid():  # Validating the form.
                username_form.save()  # If valid, save the new username.
                # Display a success message to the user.
                messages.success(request, "Your username has been updated!")
        else:
            # If it's not a username change request, initialize the form with the current user instance.
            username_form = UsernameChangingForm(instance=request.user)
    else:
        # For a GET request, initialize both forms without POST data.
        password_form = PasswordChangingForm(request.user)
        username_form = UsernameChangingForm(instance=request.user)

    # Rendering the 'settings.html' template with the context containing both forms.
    return render(
        request,
        "app/settings.html",
        {"password_form": password_form, "username_form": username_form},
    )


@login_required
def edit_share_space(request, space_id):
    share_space = get_object_or_404(ShareSpace, id=space_id)

    if not share_space.is_owner(request.user):
        messages.error(request, "You cannot edit ShareSpace's you do not own!")
        return redirect("home")

    if request.method == "POST":
        form = EditShareSpaceForm(request.POST, instance=share_space)
        if form.is_valid():
            form.save()
            messages.success(request, "ShareSpace successfully edited!")
            return redirect("view_share_space", space_id=space_id)
    else:
        form = EditShareSpaceForm(instance=share_space)

    return render(
        request, "app/edit_share_space.html", {"form": form, "share_space": share_space}
    )
