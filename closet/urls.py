from django.urls import path
from . import views

app_name = "closet"

urlpatterns = [
    path("", views.show_closet, name="show_closet"),
    path("add/", views.add_item, name="add_item"),
    path("item/<int:item_id>/", views.show_item_detail, name="show_item_detail"),
]