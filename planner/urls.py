from django.urls import path
from . import views

app_name = "planner"

urlpatterns = [
    path("", views.show_planner, name="show_planner"),
    path("outfits/", views.outfit_options, name="outfit_options"),
    path("weather/", views.current_weather, name="current_weather"),
    path("week-state/", views.week_state, name="week_state"),
    path("plan/save/", views.save_plan, name="save_plan"),
    path("plan/clear/", views.clear_plan, name="clear_plan"),
    path("laundry-days/", views.save_laundry_days, name="save_laundry_days"),
]
