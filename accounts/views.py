from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            # 🔒 BLOCK REMOVED / DEACTIVATED EMPLOYEES
            if not user.is_active:
                messages.error(
                    request,
                    "Your account has been deactivated. Please contact admin."
                )
                return redirect('login')

            login(request, user)
            return redirect('post_login_redirect')

        else:
            messages.error(request, 'Invalid email or password')

    return render(request, 'accounts/login.html')



def logout_view(request):
    logout(request)
    return redirect('login')

def post_login_redirect(request):
    user = request.user

    if user.role == 'ADMIN':
        return redirect('admin_dashboard')
    else:
        return redirect('employee_dashboard')


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('post_login_redirect')
    return redirect('login')
