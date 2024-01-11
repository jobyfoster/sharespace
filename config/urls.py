"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app import views as app_views
from users import views as user_views
from admin_panel import views as admin_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # User Views
    path("register/", user_views.register, name="register"),
    path("login/", user_views.signin, name="login"),
    path("logout/", user_views.log_out, name="logout"),
    # App Views
    path("settings/", app_views.settings_view, name="settings"),
    path("", app_views.home, name="home"),
    path("upload/", app_views.upload, name="upload"),
    path("spaces/", app_views.user_spaces, name="user_spaces"),
    path("space/<str:space_id>/", app_views.view_share_space, name="view_share_space"),
    path(
        "space-password/<str:space_id>/",
        app_views.enter_space_password,
        name="space_password",
    ),
    path("download/<str:file_id>/", app_views.download_file_view, name="download"),
    path("report-file/<str:file_id>/", app_views.report_file, name="report_file"),
    path("report-space/<str:space_id>/", app_views.report_space, name="report_space"),
    path("delete-file/<str:file_id>/", app_views.delete_file, name="delete_file"),
    path("delete-space/<str:space_id>/", app_views.delete_space, name="delete_space"),
    path(
        "favorite-space/<str:space_id>/",
        app_views.favorite_space,
        name="favorite_space",
    ),
    path(
        "unfavorite-space/<str:space_id>/",
        app_views.unfavorite_space,
        name="unfavorite_space",
    ),
    # Admin Views
    path("admin-panel/", admin_views.admin_panel, name="admin_panel"),
    path(
        "admin-panel/unreviewed-space-reports/",
        admin_views.view_unreviewed_space_reports,
        name="admin_review_new_space_reports",
    ),
    path(
        "admin-panel/reviewed-space-reports/",
        admin_views.view_reviewed_space_reports,
        name="admin_review_reviewed_space_reports",
    ),
    path(
        "admin-panel/unreviewed-file-reports/",
        admin_views.view_unreviewed_file_reports,
        name="admin_review_new_file_reports",
    ),
    path(
        "admin-panel/reviewed-file-reports/",
        admin_views.view_reviewed_file_reports,
        name="admin_review_reviewed_file_reports",
    ),
    path(
        "admin-panel/review-file-report/no-action-taken/<int:user_id>/<int:report_id>/",
        admin_views.review_file_no_action,
        name="review_file_no_action",
    ),
    path(
        "admin-panel/review-file-report/action-taken/<int:user_id>/<int:report_id>/",
        admin_views.review_file_action_taken,
        name="review_file_action_taken",
    ),
    path(
        "admin-panel/review-space-report/no-action-taken/<int:user_id>/<int:report_id>/",
        admin_views.review_space_no_action,
        name="review_space_no_action",
    ),
    path(
        "admin-panel/review-space-report/action-taken/<int:user_id>/<int:report_id>/",
        admin_views.review_space_action_taken,
        name="review_space_action_taken",
    ),
    path(
        "admin-panel/audit-log/",
        admin_views.audit_log,
        name="audit_log",
    ),
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
