from django.urls import path

from .api_views import ClosetItemDetailAPIView, ClosetItemListCreateAPIView

app_name = "closet_api"

urlpatterns = [
    path("", ClosetItemListCreateAPIView.as_view(), name="item_list_create"),
    path("<int:pk>/", ClosetItemDetailAPIView.as_view(), name="item_detail"),
]
