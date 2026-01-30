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
    total_employees = User.objects.filter(
    role='EMPLOYEE',
    is_active=True
    ).count()


    # Total check-ins (created forms)
    total_checkins = CheckInForm.objects.count()

    # Check-in assignment status counts
    total_assigned = CheckInAssignment.objects.count()
    submitted = CheckInAssignment.objects.filter(
    status='SUBMITTED'
    ).count()

    pending = CheckInAssignment.objects.filter(
    status='SUBMITTED',
    review_status='PENDING'
    ).count()

    reviewed = CheckInAssignment.objects.filter(
    status='SUBMITTED',
    review_status='REVIEWED'
    ).count()


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


from django.core.mail import send_mail
from django.conf import settings

@login_required
def add_employee(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        return redirect('employee_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # ✅ NEW LOGIC — email must contain `.todoit`
        if ".todoit" not in email:
            messages.error(
                request,
                "Email must contain '.todoit'. Please use a valid company email."
            )
            return redirect("add_employee")

        # ❌ existing logic (unchanged)
        if User.objects.filter(email=email).exists():
            messages.error(
                request,
                "Employee with this email already exists."
            )
            return redirect("add_employee")

        # ❌ existing logic (unchanged)
        user = User.objects.create_user(
            email=email,
            password=password,
            role='EMPLOYEE'
        )

        # ✅ NEW LOGIC — send email with password ONLY
        send_mail(
            subject="Your 15-Five Employee Account",
            message=(
                "Your employee account has been created successfully.\n\n"
                f"Password: {password}\n\n"
                "Please keep this password secure."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect('admin_dashboard')

    return render(request, 'core/add_employee.html')



@login_required
def employee_list(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        return redirect('employee_dashboard')

    employees = User.objects.filter(
    role='EMPLOYEE',
    is_active=True
).order_by('-created_at')


    return render(
        request,
        'core/employee_list.html',
        {'employees': employees}
    )


# ================= EMPLOYEE VIEWS =================

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from checkins.models import CheckInAssignment


@login_required
def employee_dashboard(request):
    # 🔒 Block deactivated / removed employees
    if not request.user.is_active:
        return redirect("login")

    # 🔐 Role safety
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')

    # All assignments for this employee
    assignments = (
        CheckInAssignment.objects
        .filter(employee=request.user)
        .select_related('checkin_form')
    )

    # ✅ Submitted check-ins
    submitted_checkins = assignments.filter(status="SUBMITTED")

    # ✅ Pending + Partially filled (DRAFT / PARTIAL)
    pending_checkins = assignments.filter(
        status__in=["PENDING", "PARTIAL"]
    )

    context = {
        # KPI
        "submitted_count": submitted_checkins.count(),

        # Dashboard sections
        "pending_checkins": pending_checkins.order_by("assigned_at"),
        "submitted_checkins": submitted_checkins.order_by("-submitted_at")[:3],
    }

    return render(
        request,
        "core/employee_dashboard.html",
        context
    )




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from checkins.models import CheckInAssignment


@login_required
def employee_checkins(request):
    # 🔒 Block deactivated / removed employees
    if not request.user.is_active:
        return redirect("login")

    # 🔐 Role check
    if request.user.role != 'EMPLOYEE':
        return redirect('admin_dashboard')

    # 📋 Fetch ALL assignments for this employee
    assignments = (
        CheckInAssignment.objects
        .filter(employee=request.user)
        .select_related('checkin_form')
        .order_by("-assigned_at")
    )

    return render(
        request,
        "core/employee_checkins.html",
        {
            "assignments": assignments
        }
    )



from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from checkins.models import (
    CheckInAssignment,
    CheckInFormQuestion,
    CheckInAnswer,
)
from checkins.services.slack import send_admin_all_submitted_dm


@login_required
def employee_checkin_form(request, assignment_id):
    # 🔒 Block removed / inactive employees
    if not request.user.is_active:
        return redirect("login")

    assignment = get_object_or_404(
        CheckInAssignment,
        id=assignment_id,
        employee=request.user
    )

    checkin_form = assignment.checkin_form

    # ✅ ONLY questions selected for this check-in
    questions = (
        CheckInFormQuestion.objects
        .filter(checkin_form=checkin_form)
        .select_related("question")
        .order_by("id")
    )

    # ✅ Expiry check (NO deadline usage)
    today = timezone.now().date()
    is_expired = today > checkin_form.end_date

    if request.method == "POST":
        if is_expired:
            return redirect("employee_dashboard")

        action = request.POST.get("action")

        has_any_answer = False

        # 💾 Save answers
        for fq in questions:
            text = request.POST.get(
                f"question_{fq.question.id}", ""
            ).strip()

            if text:
                has_any_answer = True

            CheckInAnswer.objects.update_or_create(
                assignment=assignment,
                question=fq.question,
                defaults={
                    "employee": request.user,
                    "answer_text": text
                }
            )

        # 📝 SAVE DRAFT
        if action == "draft":
            if has_any_answer:
                assignment.status = "PARTIAL"
                assignment.save()

        # ✅ SUBMIT CHECK-IN
        elif action == "submit":
            assignment.status = "SUBMITTED"
            assignment.submitted_at = timezone.now()
            assignment.save()

            # 🔔 Notify admin if ALL employees submitted
            total = CheckInAssignment.objects.filter(
                checkin_form=checkin_form
            ).count()

            submitted = CheckInAssignment.objects.filter(
                checkin_form=checkin_form,
                status="SUBMITTED"
            ).count()

            if total == submitted:
                admin = checkin_form.created_by
                profile = getattr(admin, "employeeprofile", None)

                if profile and profile.slack_user_id:
                    send_admin_all_submitted_dm(
                        slack_user_id=profile.slack_user_id,
                        title=checkin_form.title,
                        start_date=checkin_form.start_date,
                        end_date=checkin_form.end_date
                    )

        return redirect("employee_dashboard")

    # 🧠 Existing answers for prefill
    existing_answers = {
        a.question_id: a.answer_text
        for a in assignment.answers.all()
    }

    return render(
        request,
        "checkins/employee_checkin_form.html",
        {
            "assignment": assignment,
            "questions": questions,
            "existing_answers": existing_answers,
            "is_expired": is_expired,
            "period": f"{checkin_form.start_date} → {checkin_form.end_date}",
        }
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

        # ❌ existing logic (unchanged)
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect("employee_settings")

        # ❌ existing logic (unchanged)
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect("employee_settings")

        # ✅ NEW LOGIC — empty password check
        if not new_password:
            messages.error(request, "New password cannot be empty.")
            return redirect("employee_settings")

        # ✅ NEW LOGIC — minimum length safety
        if len(new_password) < 8:
            messages.error(
                request,
                "Password must be at least 8 characters long."
            )
            return redirect("employee_settings")

        # ✅ existing logic (unchanged)
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
    # 🔒 Block deactivated / removed employees
    if not request.user.is_active:
        return redirect("login")

    # 🔐 Role safety (extra protection)
    if request.user.role != "EMPLOYEE":
        return redirect("admin_dashboard")

    # Ensure profile exists
    profile, _ = EmployeeProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.email.split("@")[0]
        }
    )

    # ✏️ Update full name
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()

        if full_name:
            profile.full_name = full_name
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


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from accounts.models import User

@login_required
def remove_employee(request, user_id):
    if request.user.role != "ADMIN":
        return redirect("admin_dashboard")

    employee = get_object_or_404(User, id=user_id, role="EMPLOYEE")

    # Soft delete
    employee.is_active = False
    employee.save()

    messages.success(request, "Employee removed successfully.")

    return redirect("employee_list")
@login_required
def admin_employee_checkins(request, user_id):
    # 🔐 Admin-only access
    if not request.user.is_superuser and request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    employee = get_object_or_404(
        User,
        id=user_id,
        role="EMPLOYEE"
    )

    assignments = (
        CheckInAssignment.objects
        .filter(employee=employee)
        .select_related("checkin_form")
        .order_by("-assigned_at")
    )

    return render(
        request,
        "core/admin_employee_checkins.html",
        {
            "employee": employee,
            "assignments": assignments,
        }
    )
