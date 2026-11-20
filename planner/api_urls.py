from django.urls import path

from . import api_views

app_name = "planner_api"

urlpatterns = [
    path("week/", api_views.PlannerWeekAPIView.as_view(), name="week"),
    path("outfits/", api_views.PlannerOutfitsAPIView.as_view(), name="outfits"),
    path("plans/", api_views.PlannerPlanAPIView.as_view(), name="plans"),
    path("plans/<str:day>/", api_views.PlannerPlanDetailAPIView.as_view(), name="plan_detail"),
    path("settings/", api_views.PlannerSettingsAPIView.as_view(), name="settings"),
    path("weather/current/", api_views.PlannerCurrentWeatherAPIView.as_view(), name="weather_current"),
    path("weather/forecast/", api_views.PlannerForecastAPIView.as_view(), name="weather_forecast"),
    path("locations/search/", api_views.PlannerLocationSearchAPIView.as_view(), name="location_search"),
]
