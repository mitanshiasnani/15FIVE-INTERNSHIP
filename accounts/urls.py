# accounts/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home_redirect, name='home'),
    path('post-login-redirect/', views.post_login_redirect, name='post_login_redirect'),
    
    # 2FA
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),
    
    # Password Reset
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # Session Management
    path('check-session/', views.check_session_timeout, name='check_session_timeout'),
]
