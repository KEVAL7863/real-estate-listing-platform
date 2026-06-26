from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("properties/", views.property_list, name="property_list"),
    path("properties/add/", views.property_create, name="property_create"),
    path("favorites/", views.my_favorites, name="my_favorites"),
    path("favorite/<int:pk>/toggle/", views.toggle_favorite, name="toggle_favorite"),
    # Admin moderation
    path("manage/properties/", views.manage_properties, name="manage_properties"),
    path("manage/users/", views.manage_users, name="manage_users"),
    path("manage/property/<int:pk>/<str:action>/", views.moderate_property, name="moderate_property"),
    path("image/<int:pk>/delete/", views.image_delete, name="image_delete"),
    # Detail / edit / delete use slugs (keep last to avoid clashes)
    path("property/<slug:slug>/", views.property_detail, name="property_detail"),
    path("property/<slug:slug>/edit/", views.property_edit, name="property_edit"),
    path("property/<slug:slug>/delete/", views.property_delete, name="property_delete"),
]
