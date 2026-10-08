from django.urls import path

from community.views import (
    create_comment,
    create_post,
    delete_comment,
    delete_post,
    edit_comment,
    edit_post,
    show_community,
)

app_name = "community"

urlpatterns = [
    path("", show_community, name="show_community"),
    path("post/create/", create_post, name="create_post"),
    path("post/<int:post_id>/edit/", edit_post, name="edit_post"),
    path("post/<int:post_id>/delete/", delete_post, name="delete_post"),
    path("post/<int:post_id>/comment/", create_comment, name="create_comment"),
    path("comment/<int:comment_id>/edit/", edit_comment, name="edit_comment"),
    path("comment/<int:comment_id>/delete/", delete_comment, name="delete_comment"),
]