from django.urls import path
from . import views

app_name = "planner"

urlpatterns = [
    path("", views.show_planner, name="show_planner"),
]