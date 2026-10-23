from django.urls import path
from . import views

app_name = "mixmatch"

urlpatterns = [
    path("", views.show_mixmatch, name="show_mixmatch"),
    path("save/", views.save_outfit, name="save_outfit"),
    path("<int:outfit_id>/edit/", views.edit_outfit, name="edit_outfit"),
    path("<int:outfit_id>/delete/", views.delete_outfit, name="delete_outfit"),
]