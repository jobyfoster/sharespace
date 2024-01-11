from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from app.models import (
    FileReport,
    ShareSpace,
    SpaceReport,
    ReportStatus,
    get_file_reports,
    get_space_reports,
    get_reviewed_file_reports,
    get_reviewed_space_reports,
    get_under_review_file_reports,
    get_under_review_space_reports,
    review_report,
)
from django.core.paginator import Paginator
from .models import (
    AuditLog,
    create_audit_log_for_file_report_change,
    create_audit_log_for_space_report_change,
)
from django.http import HttpResponseRedirect
from .decorators import group_required


@group_required("Admin")  # Ensures only users in the "Admin" group can access this view
def admin_panel(request):
    # Redirects to the view for reviewing new reports
    return redirect("admin_review_new_file_reports")


@group_required("Admin")
def view_unreviewed_file_reports(request):
    # Fetches a list of reports that are currently under review
    unreviewed_reports = get_under_review_file_reports()
    # Renders a template with the unreviewed reports
    return render(
        request,
        "admin_panel/unreviewed_file_reports.html",
        {"reports": unreviewed_reports},
    )


@group_required("Admin")
def review_file_no_action(request, user_id, report_id):
    # This view handles the case where no action is taken on a report
    if request.POST:
        # Fetches the report or returns a 404 if not found
        report = get_object_or_404(FileReport, id=report_id)
        # Fetches the user who reviewed the report
        reviewed_by = User.objects.get(id=user_id)
        # Updates the report status to indicate no action was taken
        review_report(report, reviewed_by, ReportStatus.REVIEWED_NO_ACTION)

        # Creates an audit log for this report change
        create_audit_log_for_file_report_change(user=request.user, report=report)
        # Shows a success message to the admin
        messages.success(
            request,
            f'File Report #{report_id} has been marked "No Action Taken" by {reviewed_by.username}!',
        )

        # Redirects back to the previous page
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@group_required("Admin")
def review_file_action_taken(request, user_id, report_id):
    # This view is for marking a report as having action taken
    if request.POST:
        # Fetches the report, 404 if not found
        report = get_object_or_404(FileReport, id=report_id)
        # Gets the user who reviewed the report
        reviewed_by = User.objects.get(id=user_id)
        # Marks the report as having action taken
        review_report(report, reviewed_by, ReportStatus.REVIEWED_ACTION_TAKEN)

        # Creates an audit log for the report status change
        create_audit_log_for_file_report_change(user=request.user, report=report)
        # Notifies the admin of the successful action
        messages.success(
            request,
            f'Report #{report_id} has been marked "Action Taken" by {reviewed_by.username}!',
        )

        # Redirects back to the previous page
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@group_required("Admin")
def view_reviewed_file_reports(request):
    # Retrieves all reports that have been reviewed
    reviewed_reports = get_reviewed_file_reports()

    # Renders the page with the reviewed reports
    return render(
        request, "admin_panel/reviewed_file_reports.html", {"reports": reviewed_reports}
    )


@group_required("Admin")
def view_all_file_reports(request):
    file_reports = get_file_reports()

    return render(
        request, "admin_panel/all_file_reports.html", {"reports": file_reports}
    )


@group_required("Admin")
def view_unreviewed_space_reports(request):
    # Fetches a list of reports that are currently under review
    unreviewed_reports = get_under_review_space_reports()
    # Renders a template with the unreviewed reports
    return render(
        request,
        "admin_panel/unreviewed_space_reports.html",
        {"reports": unreviewed_reports},
    )


@group_required("Admin")
def view_reviewed_space_reports(request):
    # Fetches a list of reports that are currently under review
    reviewed_reports = get_reviewed_space_reports()

    # Renders a template with the unreviewed reports
    return render(
        request,
        "admin_panel/reviewed_space_reports.html",
        {"reports": reviewed_reports},
    )


@group_required("Admin")
def view_all_space_reports(request):
    space_reports = get_space_reports()

    return render(
        request, "admin_panel/all_space_reports.html", {"reports": space_reports}
    )


@group_required("Admin")
def review_space_no_action(request, user_id, report_id):
    # This view handles the case where no action is taken on a report
    if request.POST:
        # Fetches the report or returns a 404 if not found
        report = get_object_or_404(SpaceReport, id=report_id)
        # Fetches the user who reviewed the report
        reviewed_by = User.objects.get(id=user_id)
        # Updates the report status to indicate no action was taken
        review_report(report, reviewed_by, ReportStatus.REVIEWED_NO_ACTION)

        # Creates an audit log for this report change
        create_audit_log_for_space_report_change(user=request.user, report=report)
        # Shows a success message to the admin
        messages.success(
            request,
            f'ShareSpace Report #{report_id} has been marked "No Action Taken" by {reviewed_by.username}!',
        )

        # Redirects back to the previous page
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@group_required("Admin")
def review_space_action_taken(request, user_id, report_id):
    # This view is for marking a report as having action taken
    if request.POST:
        # Fetches the report, 404 if not found
        report = get_object_or_404(SpaceReport, id=report_id)
        # Gets the user who reviewed the report
        reviewed_by = User.objects.get(id=user_id)
        # Marks the report as having action taken
        review_report(report, reviewed_by, ReportStatus.REVIEWED_ACTION_TAKEN)

        # Creates an audit log for the report status change
        create_audit_log_for_file_report_change(user=request.user, report=report)
        # Notifies the admin of the successful action
        messages.success(
            request,
            f'Report #{report_id} has been marked "Action Taken" by {reviewed_by.username}!',
        )

        # Redirects back to the previous page
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@group_required("Admin")
def audit_log(request):
    # Fetches all audit logs, ordered by the creation date (newest first)
    logs_list = AuditLog.objects.all().order_by("-created_at")
    # Sets up pagination for the logs, displaying 10 per page
    paginator = Paginator(logs_list, 10)

    # Gets the current page number from the request
    page_number = request.GET.get("page")
    logs = paginator.get_page(page_number)  # Gets the logs for the current page

    # Renders the audit log page with the paginated logs
    return render(request, "admin_panel/audit_log.html", {"logs": logs})
