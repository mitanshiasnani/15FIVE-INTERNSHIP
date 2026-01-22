# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('', include('accounts.urls')),

    # Core dashboard
    path('dashboard/', include('core.urls')),

    # Check-ins (MUST have prefix)
    path('checkins/', include('checkins.urls')),
]

