from django.contrib import admin

from .models import Property, PropertyImage, Favorite


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "title", "owner", "city", "property_type", "listing_type",
        "price", "status", "is_featured", "views", "created_at",
    )
    list_filter = ("status", "property_type", "listing_type", "is_featured", "city")
    search_fields = ("title", "city", "address", "description")
    list_editable = ("status", "is_featured")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PropertyImageInline]
    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="Approve selected properties")
    def approve_selected(self, request, queryset):
        queryset.update(status=Property.Status.APPROVED)

    @admin.action(description="Reject selected properties")
    def reject_selected(self, request, queryset):
        queryset.update(status=Property.Status.REJECTED)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "property", "created_at")
