from django.urls import path

from community.views import (
    create_post, 
    show_community,
    create_comment
)

app_name = "community"

urlpatterns = [
    path("", show_community, name="show_community"),
    path("create/", create_post, name="create_post"),
    path("post/<int:post_id>/comment/", create_comment, name="create_comment"),
]