from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.contrib import messages
from .forms import FileUploadForm
from .models import (
    ShareSpace,
    UploadedFile,
    Report,
    get_user_files,
    create_report,
    create_shared_space,
)
from django.conf import settings
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

            shared_space = create_shared_space(
                user=request.user, title=title, description=description
            )

            for file in files:
                UploadedFile.objects.create(
                    share_space=shared_space,
                    user=request.user,
                    file=file,
                )
                print(f"Uploaded new file")

            messages.success(request, "Share space successfully created!")
            return redirect("view_shared_space", space_id=shared_space.id)
    else:
        form = FileUploadForm()

    return render(request, "app/upload_file.html", {"form": form})


@login_required
def view_share_space(request, space_id):
    share_space = get_object_or_404(ShareSpace, id=space_id)
    share_space_files = share_space.files.all()

    return render(
        request,
        "app/share_space.html",
        context={"share_space": share_space, "files": share_space_files},
    )


@login_required
def download_file_view(request, file_id):
    file_instance = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    if not file_instance.file:
        raise Http404("File does not exist")

    return render(request, "app/download_file.html", {"file": file_instance})


@login_required
def user_files(request):
    users_files = get_user_files(user=request.user)

    return render(request, "app/user_files.html", {"files": users_files})


@login_required
def report_file(request, file_id):
    reported_by = request.user
    reported_file = get_object_or_404(UploadedFile, id=file_id)
    user_reported = reported_file.user

    if reported_by == user_reported:
        messages.error(request, "You cannot report a file that you own.")
        return redirect("download", file_id=file_id)

    create_report(
        reported_by=reported_by,
        user_reported=user_reported,
        file_reported=reported_file,
    )

    messages.success(request, "Report successfully submitted!")
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
