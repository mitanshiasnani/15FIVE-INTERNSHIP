from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import User, EmployeeProfile
from checkins.models import CheckInAssignment, Question


# ================= ADMIN VIEWS =================

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        return redirect('employee_dashboard')

    total_employees = User.objects.filter(role='EMPLOYEE').count()
    total_checkins = 247  # static for now

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

    return render(request, 'core/admin_profile.html', {'user': request.user})


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




# ================= EMPLOYEE VIEWS =================

from django.utils import timezone

@login_required
def employee_dashboard(request):
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')

    assignments = CheckInAssignment.objects.filter(
        employee=request.user
    ).select_related('checkin_form')

    submitted_checkins = assignments.filter(status='SUBMITTED')
    pending_checkins = assignments.filter(status='PENDING')

    context = {
        "submitted_count": submitted_checkins.count(),
        "pending_checkins": pending_checkins,
        "submitted_checkins": submitted_checkins[:3],  # optional: recent ones
    }

    return render(
        request,
        "core/employee_dashboard.html",
        context
    )




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
def employee_checkin_form(request, assignment_id):
    assignment = get_object_or_404(
        CheckInAssignment,
        id=assignment_id,
        employee=request.user
    )

    questions = Question.objects.all().order_by("id")

    # ✅ Build a PROPER dictionary: {question_id: answer_text}
    existing_answers = {
        answer.question_id: answer.answer_text
        for answer in assignment.answers.all()
    }

    context = {
        "assignment": assignment,
        "questions": questions,
        "existing_answers": existing_answers,
        "is_expired": assignment.checkin_form.deadline.date() < timezone.now().date(),
    }

    return render(
        request,
        "checkins/employee_checkin_form.html",
        context
    )



@login_required
def employee_history(request):
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')

    return render(request, "core/employee_history.html")

from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def employee_settings(request):
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        user = request.user

        # 1️⃣ Verify current password
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect("employee_settings")

        # 2️⃣ Validate new password match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect("employee_settings")

        # 3️⃣ Update password
        user.set_password(new_password)
        user.save()

        # 4️⃣ LOGOUT IMMEDIATELY (🔥 THIS IS THE KEY)
        logout(request)

        # 5️⃣ Redirect to login page
        messages.success(
            request,
            "Password updated successfully. Please log in again."
        )
        return redirect("login")

    return render(request, "core/employee_settings.html")



@login_required
def employee_profile(request):
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')

    profile, created = EmployeeProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.email.split("@")[0],
            "designation": "Software Engineer",
            "department": "Engineering"
        }
    )

    return render(
        request,
        "core/employee_profile.html",
        {"profile": profile}
    )

