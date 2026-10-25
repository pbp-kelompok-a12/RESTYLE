from django.urls import path
from main.views import ( 
    show_landing_page, register, login_user, logout_user, profile_view,
    style_quiz, wishlist_view, add_wishlist_item,
    get_wishlist_detail, edit_wishlist_item, delete_wishlist_item
)

app_name = "main"

urlpatterns = [
    path("", show_landing_page, name="show_landing_page"),
    path('quiz/', style_quiz, name='style_quiz'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('profile/', profile_view, name="profile"),
    path('wishlist/', wishlist_view, name='wishlist'),
    path('wishlist/add/', add_wishlist_item, name='add_wishlist_item'),
    path('wishlist/<int:item_id>/detail/', get_wishlist_detail, name='get_wishlist_detail'),
    path('wishlist/<int:item_id>/edit/', edit_wishlist_item, name='edit_wishlist_item'),
    path('wishlist/<int:item_id>/delete/', delete_wishlist_item, name='delete_wishlist_item'),
]