from django.urls import path
from .views import login_view, logout_view, post_login_redirect, home_redirect

urlpatterns = [
    path('', home_redirect, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('redirect/', post_login_redirect, name='post_login_redirect'),
]
