from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout

from django.contrib.auth.decorators import login_required

from django.contrib import messages

# Create your views here.


def register(request):
    form = UserCreationForm()
    if request.POST:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created!")
            return redirect("login")

    return render(request, "users/register.html", {"form": form})


def signin(request):
    if request.POST:
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Successfully logged in!")
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password!")

    return render(request, "users/login.html")


@login_required
def log_out(request):
    logout(request)
    messages.success(request, "You have been logged out!")
    return redirect("home")
