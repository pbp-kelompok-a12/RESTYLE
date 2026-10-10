from django.urls import path
from . import views

app_name = "closet"

urlpatterns = [
    path("", views.show_closet, name="show_closet"),
    path("item/create/", views.create_item, name="create_item"),
]