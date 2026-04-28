# accounts/views.py - COMPLETE REWRITE with Security

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from .models import LoginAttempt, SessionTimeout, PasswordReset
import secrets


def get_client_ip(request):
    """Extract client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_rate_limit(request, email):
    """Check if user has exceeded rate limit (5 attempts per 15 mins)"""
    ip = get_client_ip(request)
    fifteen_mins_ago = timezone.now() - timedelta(minutes=15)
    
    # Count failed attempts from this IP in last 15 minutes
    recent_attempts = LoginAttempt.objects.filter(
        email=email,
        ip_address=ip,
        is_successful=False,
        timestamp__gte=fifteen_mins_ago
    ).count()
    
    return recent_attempts >= 5


def log_login_attempt(request, email, user=None, is_successful=False, reason=None):
    """Log login attempt to database"""
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    LoginAttempt.objects.create(
        user=user,
        email=email,
        ip_address=ip,
        user_agent=user_agent,
        is_successful=is_successful,
        failure_reason=reason
    )


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Secure login with rate limiting, account lockout, and 2FA"""
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, 'Invalid email or password')
            return render(request, 'accounts/login.html')
        
        # Check rate limit
        if check_rate_limit(request, email):
            log_login_attempt(request, email, is_successful=False, reason='RATE_LIMITED')
            messages.error(request, 'Invalid email or password')
            return render(request, 'accounts/login.html')
        
        # Try to find user
        try:
            user = authenticate(request, email=email, password=password)
        except Exception:
            log_login_attempt(request, email, is_successful=False, reason='INVALID_CREDENTIALS')
            messages.error(request, 'Invalid email or password')
            return render(request, 'accounts/login.html')
        
        if user is not None:
            # Check if account is locked
            if user.is_account_locked():
                log_login_attempt(request, email, user=user, is_successful=False, reason='ACCOUNT_LOCKED')
                messages.error(request, 'Invalid email or password')
                return render(request, 'accounts/login.html')
            
            # Check if account is active
            if not user.is_active:
                log_login_attempt(request, email, user=user, is_successful=False, reason='ACCOUNT_INACTIVE')
                messages.error(request, 'Invalid email or password')
                return render(request, 'accounts/login.html')
            
            # Check if 2FA is enabled
            if user.two_factor_enabled:
                # Generate 2FA code and send to user
                code = user.generate_2fa_secret()
                send_2fa_code(user, code)  # See function below
                
                # Store email in session for 2FA verification
                request.session['2fa_email'] = email
                request.session['2fa_user_id'] = user.id
                request.session['2fa_attempts'] = 0
                
                messages.info(request, f'2FA code sent to {user.email}')
                return redirect('verify_2fa')
            
            # Reset failed login attempts
            user.reset_login_attempts()
            
            # Clear old messages before login
            storage = messages.get_messages(request)
            storage.used = True
            
            # Login successful
            login(request, user)
            log_login_attempt(request, email, user=user, is_successful=True)
            
            # Create session timeout tracker
            SessionTimeout.objects.update_or_create(
                user=user,
                defaults={
                    'session_key': request.session.session_key,
                    'ip_address': get_client_ip(request)
                }
            )
            
            return redirect('post_login_redirect')
        
        else:
            # Invalid credentials
            log_login_attempt(request, email, is_successful=False, reason='INVALID_CREDENTIALS')
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'accounts/login.html')


def verify_2fa(request):
    """Verify 2FA code"""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        user_id = request.session.get('2fa_user_id')
        
        if not user_id:
            return redirect('login')
        
        try:
            from .models import CustomUser
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return redirect('login')
        
        # Check 2FA attempts (max 3)
        attempts = request.session.get('2fa_attempts', 0)
        if attempts >= 3:
            messages.error(request, 'Too many 2FA attempts. Please login again.')
            del request.session['2fa_email']
            del request.session['2fa_user_id']
            del request.session['2fa_attempts']
            return redirect('login')
        
        if code == user.two_factor_secret:
            # 2FA verified
            user.reset_login_attempts()
            storage = messages.get_messages(request)
            storage.used = True
            
            login(request, user)
            log_login_attempt(request, user.email, user=user, is_successful=True)
            
            # Clean up session
            del request.session['2fa_email']
            del request.session['2fa_user_id']
            del request.session['2fa_attempts']
            
            SessionTimeout.objects.update_or_create(
                user=user,
                defaults={
                    'session_key': request.session.session_key,
                    'ip_address': get_client_ip(request)
                }
            )
            
            return redirect('post_login_redirect')
        else:
            request.session['2fa_attempts'] = attempts + 1
            messages.error(request, 'Invalid 2FA code')
    
    return render(request, 'accounts/verify_2fa.html')


def send_2fa_code(user, code):
    """Send 2FA code via email (SMS can be added later)"""
    from django.core.mail import send_mail
    
    subject = '15-Five: Your 2FA Verification Code'
    message = f'''
    Your 2FA verification code is: {code}
    
    This code expires in 10 minutes.
    
    If you didn't request this, please ignore this email.
    '''
    
    try:
        send_mail(subject, message, 'noreply@15five.com', [user.email])
    except Exception as e:
        print(f"Failed to send 2FA email: {e}")


def post_login_redirect(request):
    """Redirect to appropriate dashboard based on role"""
    user = request.user
    
    if user.role == 'ADMIN':
        return redirect('admin_dashboard')
    else:
        return redirect('employee_dashboard')


def home_redirect(request):
    """Home page redirect"""
    if request.user.is_authenticated:
        return redirect('post_login_redirect')
    return redirect('login')


@login_required
@require_POST
def logout_view(request):
    """Secure logout"""
    # Clear messages
    storage = messages.get_messages(request)
    storage.used = True
    
    # Remove session timeout record
    try:
        SessionTimeout.objects.get(user=request.user).delete()
    except SessionTimeout.DoesNotExist:
        pass
    
    logout(request)
    return redirect('login')


@require_http_methods(["GET", "POST"])
def forgot_password(request):
    """Password reset request"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please enter your email address')
            return render(request, 'accounts/forgot_password.html')
        
        try:
            from .models import CustomUser
            user = CustomUser.objects.get(email=email)
            
            # Generate reset token
            user.generate_password_reset_token()
            
            # Send reset email
            send_password_reset_email(user)
            messages.success(request, 'Password reset link sent to your email')
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists (security)
            messages.success(request, 'Password reset link sent to your email')
        
        return render(request, 'accounts/forgot_password.html')
    
    return render(request, 'accounts/forgot_password.html')


def send_password_reset_email(user):
    """Send password reset email"""
    from django.core.mail import send_mail
    from django.urls import reverse
    
    reset_url = reverse('reset_password', kwargs={'token': user.password_reset_token})
    full_url = f"http://127.0.0.1:8000{reset_url}"
    
    subject = '15-Five: Password Reset Request'
    message = f'''
    Click the link below to reset your password:
    {full_url}
    
    This link expires in 24 hours.
    
    If you didn't request this, please ignore this email.
    '''
    
    try:
        send_mail(subject, message, 'noreply@15five.com', [user.email])
    except Exception as e:
        print(f"Failed to send reset email: {e}")


@require_http_methods(["GET", "POST"])
def reset_password(request, token):
    """Reset password with token"""
    try:
        from .models import CustomUser
        user = CustomUser.objects.get(password_reset_token=token)
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid or expired reset link')
        return redirect('login')
    
    # Check if token expired
    if not user.password_reset_expires or timezone.now() > user.password_reset_expires:
        messages.error(request, 'Password reset link has expired')
        user.password_reset_token = ''
        user.password_reset_expires = None
        user.save()
        return redirect('forgot_password')
    
    if request.method == 'POST':
        new_password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not new_password or new_password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'accounts/reset_password.html', {'token': token})
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return render(request, 'accounts/reset_password.html', {'token': token})
        
        # Set new password
        user.set_password(new_password)
        user.password_reset_token = ''
        user.password_reset_expires = None
        user.failed_login_attempts = 0
        user.is_locked = False
        user.save()
        
        messages.success(request, 'Password reset successful. Please login.')
        return redirect('login')
    
    return render(request, 'accounts/reset_password.html', {'token': token})


@login_required
def check_session_timeout(request):
    """AJAX endpoint to check if session has timed out"""
    try:
        session_timeout = SessionTimeout.objects.get(user=request.user)
        is_expired = session_timeout.is_session_expired(timeout_minutes=30)
        
        if is_expired:
            logout(request)
            return JsonResponse({'expired': True})
        
        # Update last activity
        session_timeout.save()
        return JsonResponse({'expired': False})
    except SessionTimeout.DoesNotExist:
        return JsonResponse({'expired': False})
