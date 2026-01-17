# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django Admin (reserved)
    path('admin/', admin.site.urls),

    # Auth (login, logout)
    path('', include('accounts.urls')),

    # Admin Dashboard (custom)
    path('dashboard/', include('core.urls')),

    # Employee check-ins
    path('', include('checkins.urls')),
]
