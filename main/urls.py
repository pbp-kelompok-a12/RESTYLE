from django.urls import path
from main.views import ( show_landing_page, register, login_user,  logout_user,  
    style_quiz, profile_view
)

app_name = "main"

urlpatterns = [
    path("", show_landing_page, name="show_landing_page"),
    path('quiz/', style_quiz, name='style_quiz'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    
]   
