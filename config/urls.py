from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from core import views as core_views

urlpatterns = [
    # ... your existing URLs ...
    path('dashboard/analytics/', core_views.analytics_dashboard, name='analytics_dashboard'),
]

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('', include('accounts.urls')),

    # ✅ LOGOUT (IMPORTANT)
    path('logout/', LogoutView.as_view(), name='logout'),

    # Core dashboard
    path('dashboard/', include('core.urls')),

    # Check-ins
    path('checkins/', include('checkins.urls')),
    path('dashboard/analytics/', core_views.analytics_dashboard, name='analytics_dashboard'),
]
