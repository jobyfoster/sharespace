from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout

from django.contrib.auth.decorators import login_required
from admin_panel.models import (
    create_audit_log_for_new_login,
    create_audit_log_for_new_user,
)
from django.contrib import messages

# Create your views here.


def register(request):
    form = UserCreationForm()  # Initializes a user creation form
    if request.method == "POST":
        # Processes the form when submitted
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Saves the new user if the form is valid
            user = form.save()
            # Displays a success message
            messages.success(request, "Account created!")
            # Logs the creation of the new user
            create_audit_log_for_new_user(user)
            # Redirects to the login page
            return redirect("login")

    # Renders the registration page with the form
    return render(request, "users/register.html", {"form": form})


def signin(request):
    if request.method == "POST":
        # Retrieves username and password from POST request
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Authenticates the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Logs the user in if authentication is successful
            login(request, user)
            # Logs the user login action
            create_audit_log_for_new_login(user)
            # Displays a success message
            messages.success(request, "Successfully logged in!")
            # Redirects to the home page
            return redirect("home")
        else:
            # Shows an error message if authentication fails
            messages.error(request, "Invalid username or password!")

    # Renders the login page
    return render(request, "users/login.html")


@login_required
def log_out(request):
    # Logs the user out
    logout(request)
    # Displays a success message
    messages.success(request, "You have been logged out!")
    # Redirects to the home page
    return redirect("home")
