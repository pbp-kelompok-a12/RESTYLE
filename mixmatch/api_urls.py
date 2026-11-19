from django.urls import path

from .api_views import (
    OutfitListCreateAPIView,
    OutfitDetailAPIView,
)

app_name = "mixmatch_api"

urlpatterns = [
    path(
        "",
        OutfitListCreateAPIView.as_view(),
        name="outfit_list_create",
    ),
    path(
        "<int:pk>/",
        OutfitDetailAPIView.as_view(),
        name="outfit_detail",
    ),
]