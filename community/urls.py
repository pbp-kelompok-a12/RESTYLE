from django.urls import path

from community.views import show_community

app_name = "community"

urlpatterns = [
    path("", show_community, name="show_community"),
]