from django.urls import path

from community.views import (
    create_comment,
    create_post,
    delete_comment,
    delete_post,
    edit_comment,
    edit_post,
    show_community,
    show_saved,
    toggle_comment_like,
    toggle_post_like,
    toggle_post_save,
    toggle_comment_like,
    toggle_follow,
)

app_name = "community"

urlpatterns = [
    path("", show_community, name="show_community"),
    path("saved/", show_saved, name="show_saved"),
    path("post/create/", create_post, name="create_post"),
    path("post/<int:post_id>/edit/", edit_post, name="edit_post"),
    path("post/<int:post_id>/delete/", delete_post, name="delete_post"),
    path("post/<int:post_id>/comment/", create_comment, name="create_comment"),
    path("post/<int:post_id>/like/", toggle_post_like, name="toggle_post_like"),
    path("post/<int:post_id>/save/", toggle_post_save, name="toggle_post_save"),
    path("comment/<int:comment_id>/edit/", edit_comment, name="edit_comment"),
    path("comment/<int:comment_id>/delete/", delete_comment, name="delete_comment"),
    path("comment/<int:comment_id>/like/", toggle_comment_like, name="toggle_comment_like"),
    path("user/<str:username>/follow/", toggle_follow, name="toggle_follow"),
]