from django.urls import path, include
from django.views.generic import RedirectView
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('guest-login/', views.guest_login, name='guest_login'),
    path('video-chat/', views.video_chat, name='video_chat'),
    path('text-chat/', views.text_chat, name='text_chat'),
    path('chat-select/', views.chat_select, name='chat_select'),
    path('profile/', views.profile, name='profile'),
    path('api/online-users/', views.get_online_users, name='get_online_users'),
    path('api/chat-history/<int:user_id>/', views.get_chat_history, name='get_chat_history'),
    path('api/upload-file/', views.upload_file, name='upload_file'),
    path('accounts/google/login/', RedirectView.as_view(url='/accounts/google/login/callback/'), name='google_login'),
]
