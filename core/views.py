from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, logout

from accounts.models import User, EmployeeProfile
from checkins.models import CheckInAssignment, Question, CheckInForm
from django.db.models import Exists, OuterRef
from checkins.models import CheckInAnswer


# ================= ADMIN VIEWS =================

@login_required
def admin_dashboard(request):
    # Access control (UNCHANGED)
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        return redirect('employee_dashboard')

    # Total employees (EMPLOYEE role only)
    total_employees = User.objects.filter(role='EMPLOYEE').count()

    # Total check-ins (created forms)
    total_checkins = CheckInForm.objects.count()

    # Check-in assignment status counts
    total_assigned = CheckInAssignment.objects.count()
    submitted = CheckInAssignment.objects.filter(status='SUBMITTED').count()
    pending = CheckInAssignment.objects.filter(status='PENDING').count()
    reviewed = CheckInAssignment.objects.filter(status='REVIEWED').count()

    return render(
        request,
        "core/admin_dashboard.html",
        {
            "total_employees": total_employees,
            "total_checkins": total_checkins,
            "total_assigned": total_assigned,
            "submitted": submitted,
            "pending": pending,
            "reviewed": reviewed,
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

from django.db.models import Exists, OuterRef

from django.db.models import Exists, OuterRef
from checkins.models import CheckInAssignment, CheckInAnswer

@login_required
def employee_dashboard(request):
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')

    assignments = CheckInAssignment.objects.filter(
        employee=request.user
    ).select_related('checkin_form')

    submitted_checkins = assignments.filter(status="SUBMITTED")

    pending_checkins = assignments.filter(
        status__in=["PENDING", "PARTIAL"]
    )

    context = {
        "submitted_count": submitted_checkins.count(),
        "pending_checkins": pending_checkins,
        "submitted_checkins": submitted_checkins.order_by("-submitted_at")[:3],
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


@login_required
def employee_settings(request):
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect("employee_settings")

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect("employee_settings")

        user.set_password(new_password)
        user.save()

        logout(request)

        messages.success(
            request,
            "Password updated successfully. Please log in again."
        )
        return redirect("login")

    return render(request, "core/employee_settings.html")

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.models import EmployeeProfile

@login_required
def employee_profile(request):
    profile, _ = EmployeeProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name", "").strip()
        profile.save()
        return redirect("employee_profile")

    return render(
        request,
        "core/employee_profile.html",
        {
            "profile": profile
        }
    )




@login_required
def admin_settings(request):
    if request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    return render(request, "core/admin_seetings.html")
