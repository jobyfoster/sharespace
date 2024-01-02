from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from app.models import (
    Report,
    get_reports,
    get_reviewed_reports,
    get_under_review_reports,
    review_report,
)
from django.http import HttpResponseRedirect
from .decorators import group_required

# Create your views here.


@group_required("Admin")
def admin_panel(request):
    return redirect("admin_review_new_reports")


@group_required("Admin")
def view_unreviewed_reports(request):
    unreviewed_reports = get_under_review_reports()
    return render(
        request, "admin_panel/unreviewed_reports.html", {"reports": unreviewed_reports}
    )


@group_required("Admin")
def report_no_action(request, user_id, report_id):
    if request.POST:
        report = get_object_or_404(Report, id=report_id)
        reviewed_by = User.objects.get(id=user_id)
        review_report(report, reviewed_by, Report.ReportStatus.REVIEWED_NO_ACTION)

        messages.success(
            request,
            f'Report #{report_id} has been marked "Reviewed - No Action Taken" by {reviewed_by.username}!',
        )

        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@group_required("Admin")
def report_action_taken(request, user_id, report_id):
    if request.POST:
        report = get_object_or_404(Report, id=report_id)
        reviewed_by = User.objects.get(id=user_id)
        review_report(report, reviewed_by, Report.ReportStatus.REVIEWED_ACTION_TAKEN)

        messages.success(
            request,
            f'Report #{report_id} has been marked "Reviewed - Action Taken" by {reviewed_by.username}!',
        )

        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@group_required("Admin")
def view_reviewed_reports(request):
    reviewed_reports = get_reviewed_reports()
    print(reviewed_reports)

    return render(
        request, "admin_panel/reviewed_reports.html", {"reports": reviewed_reports}
    )
