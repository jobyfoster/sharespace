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
    get_user_spaces,
    create_report,
    is_file_taken_down,
    create_shared_space,
    check_and_grant_access,
)

from admin_panel.models import (
    AuditLog,
    create_audit_log_for_report_change,
    create_audit_log_for_space_creation,
    create_audit_log_for_report_submitted,
)
import os


def home(request):
    return render(request, "app/home.html")


@login_required
def upload(request):
    if request.method == "POST":
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            files = form.cleaned_data["file_field"]
            visibility = form.cleaned_data["visibility"]
            password = form.cleaned_data["password"]

            share_space = create_shared_space(
                user=request.user,
                title=title,
                description=description,
                visibility=visibility,
                password=password,
            )

            for file in files:
                UploadedFile.objects.create(
                    share_space=share_space,
                    user=request.user,
                    file=file,
                )

            messages.success(request, "Share space successfully created!")
            create_audit_log_for_space_creation(request.user, share_space)
            return redirect("view_share_space", space_id=share_space.id)
    else:
        form = FileUploadForm()

    return render(request, "app/upload_file.html", {"form": form})


@login_required
def view_share_space(request, space_id):
    share_space = get_object_or_404(ShareSpace, id=space_id)

    if not share_space.is_accessible_by_user(request.user):
        if share_space.visibility == ShareSpace.VisibilityChoices.PASSWORD_PROTECTED:
            return redirect("space_password", space_id=space_id)
        elif share_space.visibility == ShareSpace.VisibilityChoices.PRIVATE:
            messages.error(
                request, "This is a private ShareSpace that you do not have access to!"
            )
            return redirect("home")

    share_space_files = share_space.files.all()

    return render(
        request,
        "app/share_space.html",
        context={"share_space": share_space, "files": share_space_files},
    )


@login_required
def enter_space_password(request, space_id):
    share_space = get_object_or_404(ShareSpace, id=space_id)
    form = ShareSpaceAccessForm()

    if (
        share_space.visibility != ShareSpace.VisibilityChoices.PASSWORD_PROTECTED
    ) and share_space.is_accessible_by_user:
        messages.success(request, "You already have access to this space")
        return redirect("view_share_space", space_id=space_id)

    if share_space.is_accessible_by_user(request.user):
        messages.success(request, "You already have access to this space")
        return redirect("view_share_space", space_id=space_id)

    if request.POST:
        form = ShareSpaceAccessForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]
            if check_and_grant_access(
                user=request.user, share_space=share_space, password=password
            ):
                return redirect("view_share_space", space_id=space_id)
            else:
                messages.error(request, "Incorrect password")

    return render(
        request, "app/enter_space_password.html", {"form": form, "space": share_space}
    )


@login_required
def download_file_view(request, file_id):
    file_instance = get_object_or_404(UploadedFile, id=file_id)

    if not file_instance.file:
        raise Http404("File does not exist")

    if is_file_taken_down(file_instance):
        report = Report.objects.get(file_reported=file_instance)
        return render(request, "app/file_taken_down.html", {"report": report})

    return render(request, "app/download_file.html", {"file": file_instance})


@login_required
def user_spaces(request):
    users_spaces = get_user_spaces(user=request.user)

    return render(request, "app/user_files.html", {"users_spaces": users_spaces})


@login_required
def report_file(request, file_id):
    reported_by = request.user
    reported_file = get_object_or_404(UploadedFile, id=file_id)
    user_reported = reported_file.user

    if reported_by == user_reported:
        messages.error(request, "You cannot report a file that you own.")
        return redirect("download", file_id=file_id)

    new_report = create_report(
        reported_by=reported_by,
        user_reported=user_reported,
        file_reported=reported_file,
    )

    messages.success(request, "Report successfully submitted!")
    create_audit_log_for_report_submitted(new_report)
    return redirect("download", file_id=file_id)


@login_required
def delete_file(request, file_id):
    user = request.user
    file = get_object_or_404(UploadedFile, id=file_id)

    is_owner = file.is_owner(user)

    if not is_owner:
        messages.error(request, "You do not own this file!")
        return redirect("home")

    file.delete()

    messages.success(request, "File deleted successfully!")
    return redirect("home")


@login_required
def delete_space(request, space_id):
    user = request.user
    space = get_object_or_404(ShareSpace, id=space_id)

    is_owner = space.is_owner(user)

    if not is_owner:
        messages.error(request, "You do not own this space!")
        return redirect("view_share_space", space_id=space_id)

    space.delete()

    messages.success(request, "Space deleted successfully!")
    return redirect("user_spaces")
