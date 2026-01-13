from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import User
from checkins.models import CheckInAssignment, Question


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        return redirect('employee_dashboard')

    total_employees = User.objects.filter(role='EMPLOYEE').count()
    total_checkins = 247  # static for now (real data in Module 4)

    recent_activities = [
        {"text": "New employee added: Sarah Johnson", "time": "2 hours ago"},
        {"text": "Check-in completed by Michael Chen", "time": "5 hours ago"},
        {"text": "Check-in completed by Emily Rodriguez", "time": "1 day ago"},
        {"text": "New employee added: David Park", "time": "2 days ago"},
    ]

    return render(
        request,
        "core/admin_dashboard.html",
        {
            "total_employees": total_employees,
            "total_checkins": total_checkins,
            "recent_activities": recent_activities,
        }
    )



@login_required
def admin_profile(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        return redirect('employee_dashboard')

    return render(
        request,
        'core/admin_profile.html',
        {'user': request.user}
    )

@login_required
def add_employee(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        return redirect('employee_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            return HttpResponse("Employee with this email already exists")

        User.objects.create_user(
            email=email,
            password=password,
            role='EMPLOYEE'
        )

        return redirect('admin_dashboard')

    return render(request, 'core/add_employee.html')

@login_required
def employee_list(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        return redirect('employee_dashboard')

    employees = User.objects.filter(role='EMPLOYEE').order_by('-created_at')


    return render(
        request,
        'core/employee_list.html',
        {'employees': employees}
    )



@login_required
def employee_dashboard(request):
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')

    return render(request, "core/employee_dashboard.html")
@login_required
def employee_checkins(request):
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')

    assignments = CheckInAssignment.objects.filter(
        employee=request.user
    ).select_related('checkin_form')

    return render(
        request,
        "core/employee_checkins.html",
        {"assignments": assignments}
    )



@login_required
def employee_history(request):
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')
    return render(request, "core/employee_history.html")


@login_required
def employee_settings(request):
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')
    return render(request, "core/employee_settings.html")

@login_required
def employee_profile(request):
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')

    return render(request, 'core/employee_profile.html')
@login_required
def employee_checkin_form(request, assignment_id):
    # Fetch assignment
    assignment = get_object_or_404(CheckInAssignment, id=assignment_id)

    # Fetch all questions (for now, load all)
    questions = Question.objects.all().order_by('id')

    context = {
        'assignment': assignment,
        'questions': questions,
    }

    return render(
        request,
        'core/employee_checkin_form.html',
        context
    )