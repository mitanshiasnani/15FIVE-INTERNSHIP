# accounts/models.py - PROPERLY MERGED VERSION

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)
from django.utils import timezone
from datetime import timedelta
import secrets
import string


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role='EMPLOYEE'):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(
            email=email,
            password=password,
            role='ADMIN'
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with security features
    Extends your original User model with security fields
    """
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('EMPLOYEE', 'Employee'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ SECURITY FIELDS - Account Lockout
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    last_login_attempt = models.DateTimeField(null=True, blank=True)
    
    # ✅ SECURITY FIELDS - 2FA
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(
        max_length=10,
        choices=[('EMAIL', 'Email'), ('SMS', 'SMS')],
        default='EMAIL'
    )
    two_factor_secret = models.CharField(max_length=255, blank=True)
    
    # ✅ SECURITY FIELDS - Password Reset
    password_reset_token = models.CharField(max_length=255, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    # ✅ SECURITY METHODS
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.is_locked and self.locked_until:
            if timezone.now() < self.locked_until:
                return True
            else:
                # Unlock if lockout period has passed
                self.is_locked = False
                self.locked_until = None
                self.failed_login_attempts = 0
                self.save()
        return False
    
    def record_failed_login(self):
        """Record a failed login attempt"""
        self.failed_login_attempts += 1
        self.last_login_attempt = timezone.now()
        
        if self.failed_login_attempts >= 5:
            # Lock account for 30 minutes
            self.is_locked = True
            self.locked_until = timezone.now() + timedelta(minutes=30)
        
        self.save()
    
    def reset_login_attempts(self):
        """Reset failed login counter on successful login"""
        self.failed_login_attempts = 0
        self.last_login_attempt = timezone.now()
        self.save()
    
    def generate_password_reset_token(self):
        """Generate secure password reset token"""
        token = secrets.token_urlsafe(32)
        self.password_reset_token = token
        self.password_reset_expires = timezone.now() + timedelta(hours=24)
        self.save()
        return token
    
    def generate_2fa_secret(self):
        """Generate 2FA verification code"""
        code = ''.join(secrets.choice(string.digits) for _ in range(6))
        self.two_factor_secret = code
        self.save()
        return code


class EmployeeProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employee_profile"
    )

    full_name = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)

    reporting_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_employees"
    )

    joined_on = models.DateField(auto_now_add=True)

    slack_user_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Slack User ID (e.g. U06ABC123)"
    )

    def __str__(self):
        return self.full_name or self.user.email


# ✅ SECURITY LOGGING MODELS
class LoginAttempt(models.Model):
    """Log all login attempts (successful and failed)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='login_attempts')
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_successful = models.BooleanField(default=False)
    failure_reason = models.CharField(
        max_length=50,
        choices=[
            ('INVALID_CREDENTIALS', 'Invalid Credentials'),
            ('ACCOUNT_LOCKED', 'Account Locked'),
            ('ACCOUNT_INACTIVE', 'Account Inactive'),
            ('RATE_LIMITED', 'Rate Limited'),
            ('2FA_FAILED', '2FA Failed'),
        ],
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['email', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        status = "✓ Success" if self.is_successful else "✗ Failed"
        return f"{self.email} - {status} - {self.timestamp}"


class SessionTimeout(models.Model):
    """Track user sessions for auto-logout"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='session_timeout')
    session_key = models.CharField(max_length=40)
    last_activity = models.DateTimeField(auto_now=True)
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    
    def is_session_expired(self, timeout_minutes=30):
        """Check if session has timed out"""
        expiry_time = timezone.now() - timedelta(minutes=timeout_minutes)
        return self.last_activity < expiry_time
    
    def __str__(self):
        return f"{self.user.email} - Active"


class PasswordReset(models.Model):
    """Track password reset requests"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def is_valid(self):
        """Check if reset token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Reset for {self.user.email}"
