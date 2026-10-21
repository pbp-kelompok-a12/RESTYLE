from django.urls import path
from . import views

app_name = "mixmatch"

urlpatterns = [
    path("", views.show_mixmatch, name="show_mixmatch"),
]