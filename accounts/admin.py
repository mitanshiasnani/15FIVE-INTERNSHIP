from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'role', 'is_active', 'is_staff')
    search_fields = ('email',)
    list_filter = ('role', 'is_active')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Role & Status', {'fields': ('role', 'is_active', 'is_staff')}),
        ('Permissions', {'fields': ('is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_active'),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')

from django.contrib import admin
from .models import LoginAttempt, SessionTimeout, PasswordReset

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'ip_address', 'is_successful', 'failure_reason', 'timestamp')
    list_filter = ('is_successful', 'failure_reason', 'timestamp')
    search_fields = ('email', 'ip_address')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

@admin.register(SessionTimeout)
class SessionTimeoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'login_time', 'last_activity')
    readonly_fields = ('login_time',)

@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'is_used', 'is_valid')
    list_filter = ('is_used', 'created_at')
    readonly_fields = ('created_at',)

