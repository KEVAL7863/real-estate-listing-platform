from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PropertyForm, ImageUploadForm
from .models import Property, PropertyImage, Favorite, PropertyType, ListingType


def _apply_filters(qs, params):
    """Shared keyword/city/type/price/bed/bath filtering."""
    keyword = params.get("q", "").strip()
    city = params.get("city", "").strip()
    ptype = params.get("property_type", "").strip()
    listing = params.get("listing_type", "").strip()
    min_price = params.get("min_price", "").strip()
    max_price = params.get("max_price", "").strip()
    bedrooms = params.get("bedrooms", "").strip()
    bathrooms = params.get("bathrooms", "").strip()

    if keyword:
        qs = qs.filter(
            Q(title__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(city__icontains=keyword)
            | Q(address__icontains=keyword)
        )
    if city:
        qs = qs.filter(city__icontains=city)
    if ptype:
        qs = qs.filter(property_type=ptype)
    if listing:
        qs = qs.filter(listing_type=listing)
    if min_price.isdigit():
        qs = qs.filter(price__gte=min_price)
    if max_price.isdigit():
        qs = qs.filter(price__lte=max_price)
    if bedrooms.isdigit():
        qs = qs.filter(bedrooms__gte=bedrooms)
    if bathrooms.isdigit():
        qs = qs.filter(bathrooms__gte=bathrooms)
    return qs


def home(request):
    approved = Property.objects.filter(status=Property.Status.APPROVED)
    featured = approved.filter(is_featured=True)[:6]
    if not featured:
        featured = approved[:6]
    recent = approved.order_by("-created_at")[:6]
    cities = (
        approved.values_list("city", flat=True).distinct().order_by("city")[:12]
    )
    context = {
        "featured": featured,
        "recent": recent,
        "cities": cities,
        "property_types": PropertyType.choices,
        "stats": {
            "total": approved.count(),
            "for_sale": approved.filter(listing_type=ListingType.SALE).count(),
            "for_rent": approved.filter(listing_type=ListingType.RENT).count(),
            "cities": approved.values("city").distinct().count(),
        },
    }
    return render(request, "home.html", context)


def property_list(request):
    qs = Property.objects.filter(status=Property.Status.APPROVED)
    qs = _apply_filters(qs, request.GET)

    sort = request.GET.get("sort", "")
    if sort == "price_low":
        qs = qs.order_by("price")
    elif sort == "price_high":
        qs = qs.order_by("-price")
    else:
        qs = qs.order_by("-created_at")

    paginator = Paginator(qs, 9)
    page = paginator.get_page(request.GET.get("page"))

    # Preserve filters across pagination links
    query = request.GET.copy()
    query.pop("page", None)

    favorited_ids = set()
    if request.user.is_authenticated:
        favorited_ids = set(
            Favorite.objects.filter(user=request.user).values_list(
                "property_id", flat=True
            )
        )

    context = {
        "page_obj": page,
        "total": paginator.count,
        "querystring": query.urlencode(),
        "property_types": PropertyType.choices,
        "listing_types": ListingType.choices,
        "favorited_ids": favorited_ids,
        "filters": request.GET,
    }
    return render(request, "properties/list.html", context)


def property_detail(request, slug):
    prop = get_object_or_404(
        Property.objects.select_related("owner").prefetch_related("images"), slug=slug
    )
    # Only owner/admin can view non-approved listings
    if prop.status != Property.Status.APPROVED:
        if not request.user.is_authenticated or (
            request.user != prop.owner and not request.user.is_platform_admin
        ):
            messages.warning(request, "This property is not available.")
            return redirect("property_list")
    else:
        Property.objects.filter(pk=prop.pk).update(views=prop.views + 1)

    is_favorited = (
        request.user.is_authenticated
        and Favorite.objects.filter(user=request.user, property=prop).exists()
    )
    similar = (
        Property.objects.filter(
            status=Property.Status.APPROVED, city=prop.city
        )
        .exclude(pk=prop.pk)[:3]
    )
    return render(
        request,
        "properties/detail.html",
        {"property": prop, "is_favorited": is_favorited, "similar": similar},
    )


def _save_images(prop, files):
    for f in files:
        PropertyImage.objects.create(property=prop, image=f)


@login_required
def property_create(request):
    if not (request.user.is_owner or request.user.is_platform_admin):
        messages.error(request, "Only property owners can add listings.")
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = PropertyForm(request.POST)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.owner = request.user
            prop.save()
            _save_images(prop, request.FILES.getlist("images"))
            messages.success(
                request, "Property submitted! It will appear once an admin approves it."
            )
            return redirect("accounts:dashboard")
    else:
        form = PropertyForm()
    return render(
        request,
        "properties/form.html",
        {"form": form, "image_form": ImageUploadForm(), "title": "Add Property"},
    )


@login_required
def property_edit(request, slug):
    prop = get_object_or_404(Property, slug=slug)
    if prop.owner != request.user and not request.user.is_platform_admin:
        messages.error(request, "You can't edit this property.")
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = PropertyForm(request.POST, instance=prop)
        if form.is_valid():
            prop = form.save(commit=False)
            # Editing resets approval unless an admin is editing
            if not request.user.is_platform_admin:
                prop.status = Property.Status.PENDING
            prop.save()
            _save_images(prop, request.FILES.getlist("images"))
            messages.success(request, "Property updated.")
            return redirect("accounts:dashboard")
    else:
        form = PropertyForm(instance=prop)
    return render(
        request,
        "properties/form.html",
        {
            "form": form,
            "image_form": ImageUploadForm(),
            "title": "Edit Property",
            "property": prop,
        },
    )


@login_required
def property_delete(request, slug):
    prop = get_object_or_404(Property, slug=slug)
    if prop.owner != request.user and not request.user.is_platform_admin:
        messages.error(request, "You can't delete this property.")
        return redirect("accounts:dashboard")
    if request.method == "POST":
        prop.delete()
        messages.success(request, "Property deleted.")
        return redirect("accounts:dashboard")
    return render(request, "properties/confirm_delete.html", {"property": prop})


@login_required
def image_delete(request, pk):
    img = get_object_or_404(PropertyImage, pk=pk)
    prop = img.property
    if prop.owner == request.user or request.user.is_platform_admin:
        img.delete()
        messages.info(request, "Image removed.")
    return redirect("property_edit", slug=prop.slug)


@login_required
def toggle_favorite(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, property=prop)
    if not created:
        fav.delete()
        favorited = False
    else:
        favorited = True

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"favorited": favorited, "count": prop.favorited_by.count()}
        )
    return redirect(request.META.get("HTTP_REFERER", "property_list"))


@login_required
def my_favorites(request):
    favorites = (
        Favorite.objects.filter(user=request.user)
        .select_related("property")
        .order_by("-created_at")
    )
    paginator = Paginator(favorites, 9)
    page = paginator.get_page(request.GET.get("page"))
    fav_ids = set(favorites.values_list("property_id", flat=True))
    return render(
        request, "properties/favorites.html", {"page_obj": page, "fav_ids": fav_ids}
    )


# ---- Admin moderation ----
def _require_admin(request):
    return request.user.is_authenticated and request.user.is_platform_admin


@login_required
def moderate_property(request, pk, action):
    if not _require_admin(request):
        messages.error(request, "Admins only.")
        return redirect("accounts:dashboard")
    prop = get_object_or_404(Property, pk=pk)
    if action == "approve":
        prop.status = Property.Status.APPROVED
        messages.success(request, f"Approved: {prop.title}")
    elif action == "reject":
        prop.status = Property.Status.REJECTED
        messages.warning(request, f"Rejected: {prop.title}")
    elif action == "feature":
        prop.is_featured = not prop.is_featured
        messages.info(request, f"Toggled featured for: {prop.title}")
    prop.save()
    return redirect(request.META.get("HTTP_REFERER", "accounts:dashboard"))


@login_required
def manage_properties(request):
    if not _require_admin(request):
        messages.error(request, "Admins only.")
        return redirect("accounts:dashboard")
    qs = Property.objects.select_related("owner").order_by("-created_at")
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "dashboards/manage_properties.html",
        {"page_obj": page, "status": status, "statuses": Property.Status.choices},
    )


@login_required
def manage_users(request):
    if not _require_admin(request):
        messages.error(request, "Admins only.")
        return redirect("accounts:dashboard")
    from django.contrib.auth import get_user_model

    User = get_user_model()
    users = User.objects.order_by("-date_joined")
    paginator = Paginator(users, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboards/manage_users.html", {"page_obj": page})
