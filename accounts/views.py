from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from properties.models import Property, Favorite
from messaging.models import Message
from .forms import RegisterForm, LoginForm, ProfileForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account is ready.")
            return redirect("accounts:dashboard")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


class AppLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def dashboard_view(request):
    """Route each user to a role-specific dashboard."""
    user = request.user
    if user.is_platform_admin:
        return admin_dashboard(request)
    if user.is_owner:
        return owner_dashboard(request)
    return buyer_dashboard(request)


def owner_dashboard(request):
    properties = (
        Property.objects.filter(owner=request.user)
        .annotate(fav_count=Count("favorited_by"))
        .order_by("-created_at")
    )
    stats = {
        "total": properties.count(),
        "approved": properties.filter(status=Property.Status.APPROVED).count(),
        "pending": properties.filter(status=Property.Status.PENDING).count(),
        "rejected": properties.filter(status=Property.Status.REJECTED).count(),
        "views": sum(p.views for p in properties),
    }
    unread = Message.objects.filter(
        conversation__owner=request.user, is_read=False
    ).exclude(sender=request.user).count()
    return render(
        request,
        "dashboards/owner.html",
        {"properties": properties, "stats": stats, "unread": unread},
    )


def buyer_dashboard(request):
    favorites = (
        Favorite.objects.filter(user=request.user)
        .select_related("property")
        .order_by("-created_at")
    )
    unread = Message.objects.filter(
        conversation__buyer=request.user, is_read=False
    ).exclude(sender=request.user).count()
    return render(
        request,
        "dashboards/buyer.html",
        {"favorites": favorites, "unread": unread},
    )


def admin_dashboard(request):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    stats = {
        "total_properties": Property.objects.count(),
        "pending": Property.objects.filter(status=Property.Status.PENDING).count(),
        "approved": Property.objects.filter(status=Property.Status.APPROVED).count(),
        "rejected": Property.objects.filter(status=Property.Status.REJECTED).count(),
        "total_users": User.objects.count(),
        "owners": User.objects.filter(role=User.Role.OWNER).count(),
        "buyers": User.objects.filter(role=User.Role.BUYER).count(),
    }
    pending_properties = (
        Property.objects.filter(status=Property.Status.PENDING)
        .select_related("owner")
        .order_by("created_at")
    )
    return render(
        request,
        "dashboards/admin.html",
        {"stats": stats, "pending_properties": pending_properties},
    )


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
