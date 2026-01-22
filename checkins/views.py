from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from calendar import monthrange
from datetime import timedelta

from django.contrib.auth import get_user_model
User = get_user_model()

from .models import (
    Question,
    CheckInForm,
    CheckInFormQuestion,
    CheckInAssignment,
    CheckInAnswer,
)

from checkins.services.slack import send_checkin_assigned_dm


# -------------------------------------------------
# SAFE HELPER (NO LOGIC CHANGE)
# -------------------------------------------------
def get_slack_user_id(user):
    """
    Safely fetch slack_user_id without silent failure
    """
    try:
        return user.employeeprofile.slack_user_id
    except Exception as e:
        print("❌ SLACK PROFILE MISSING FOR:", user.email)
        return None


# -------------------------------
# ADMIN: CREATE CHECK-IN
# -------------------------------
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from calendar import monthrange
from datetime import timedelta

from accounts.models import User
from .models import (
    Question,
    CheckInForm,
    CheckInFormQuestion,
    CheckInAssignment,
)
from checkins.services.slack import send_checkin_assigned_dm


@login_required
def create_checkin(request):
    print("🔥 CREATE_CHECKIN HIT")

    if request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    questions = Question.objects.filter(is_default=True)

    if request.method == "POST":
        period = request.POST.get("period")
        start_date = timezone.datetime.strptime(
            request.POST.get("start_date"), "%Y-%m-%d"
        ).date()

        if period == "WEEKLY":
            end_date = start_date + timedelta(days=5)
        else:
            end_date = start_date.replace(
                day=monthrange(start_date.year, start_date.month)[1]
            )

        checkin = CheckInForm.objects.create(
            title=f"{period.capitalize()} Check-In",
            period=period,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user,
        )

        # QUESTIONS
        CheckInFormQuestion.objects.filter(checkin_form=checkin).delete()

        for q_id in request.POST.getlist("questions"):
            CheckInFormQuestion.objects.create(
                checkin_form=checkin,
                question_id=q_id
            )

        for text in request.POST.getlist("custom_questions[]"):
            if text.strip():
                q = Question.objects.create(
                    question_text=text.strip(),
                    is_default=False,
                    created_by=request.user
                )
                CheckInFormQuestion.objects.create(
                    checkin_form=checkin,
                    question=q
                )

        # ASSIGN ONLY (NO SLACK)
        employees = User.objects.filter(role="EMPLOYEE", is_active=True)

        for emp in employees:
            CheckInAssignment.objects.create(
                checkin_form=checkin,
                employee=emp,
                status="PENDING",
                review_status="PENDING",
            )

        return redirect("admin_checkins_list")

    return render(request, "checkins/create_checkin.html", {"questions": questions})





# -------------------------------
# EMPLOYEE: CHECK-IN LIST
# -------------------------------
@login_required
def employee_checkins(request):
    assignments = CheckInAssignment.objects.filter(employee=request.user)
    return render(
        request,
        "core/employee_checkins.html",
        {"assignments": assignments}
    )


# -------------------------------
# EMPLOYEE: CHECK-IN FORM
# -------------------------------
@login_required
def employee_checkin_form(request, assignment_id):
    assignment = get_object_or_404(
        CheckInAssignment,
        id=assignment_id,
        employee=request.user
    )

    checkin_form = assignment.checkin_form

    questions = (
        CheckInFormQuestion.objects
        .filter(checkin_form=checkin_form)
        .select_related("question")
    )

    today = timezone.now().date()
    is_expired = today > checkin_form.end_date
    is_readonly = assignment.status == "SUBMITTED" or is_expired

    if request.method == "POST":
        if is_readonly:
            return redirect("employee_dashboard")

        action = request.POST.get("action")
        has_any_answer = False

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

        if action == "draft":
            if has_any_answer and assignment.status != "SUBMITTED":
                assignment.status = "PARTIAL"
                assignment.save()

        elif action == "submit":
            assignment.status = "SUBMITTED"
            assignment.submitted_at = timezone.now()
            assignment.save()

        return redirect("employee_dashboard")

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
        }
    )


# -------------------------------
# ADMIN: CHECK-INS LIST
# -------------------------------
@login_required
def admin_checkins_list(request):
    if not request.user.is_superuser and request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    rows = []
    forms = CheckInForm.objects.order_by("-created_at")

    for form in forms:
        assignments = CheckInAssignment.objects.filter(checkin_form=form)

        rows.append({
            "form": form,
            "total": assignments.count(),
            "submitted": assignments.filter(status="SUBMITTED").count(),
            "pending_review": assignments.filter(
                status="SUBMITTED",
                review_status="PENDING"
            ).count(),
            "reviewed": assignments.filter(
                status="SUBMITTED",
                review_status="REVIEWED"
            ).count(),
        })

    return render(
        request,
        "checkins/admin/admin_checkins_list.html",
        {"rows": rows}
    )


# -------------------------------
# ADMIN: CHECK-IN DETAIL (REVIEW)
# -------------------------------
@login_required
def admin_checkin_detail(request, assignment_id):
    if request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    assignment = get_object_or_404(CheckInAssignment, id=assignment_id)

    answers = (
        CheckInAnswer.objects
        .filter(assignment=assignment)
        .select_related("question")
    )

    if request.method == "POST" and assignment.status == "SUBMITTED":
        if assignment.review_status != "REVIEWED":
            assignment.review_status = "REVIEWED"
            assignment.reviewed_at = timezone.now()
            assignment.save()

            send_mail(
                subject="Your check-in has been reviewed",
                message=(
                    f"Hi {assignment.employee.email},\n\n"
                    f"Your {assignment.checkin_form.title} has been reviewed."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[assignment.employee.email],
                fail_silently=True,
            )

        return redirect("admin_checkins_list")

    return render(
        request,
        "checkins/admin/admin_checkin_detail.html",
        {
            "assignment": assignment,
            "answers": answers,
        }
    )


# -------------------------------
# ADMIN: EMPLOYEE CHECK-INS
# -------------------------------
@login_required
def admin_employee_checkins(request, employee_id):
    if request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    employee = get_object_or_404(User, id=employee_id, role="EMPLOYEE")

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
