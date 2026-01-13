from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.models import User
from .models import (
    Question,
    CheckInForm,
    CheckInFormQuestion,
    CheckInAssignment,
    CheckInAnswer,
)
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


# -------------------------------
# ADMIN: CREATE CHECK-IN
# -------------------------------
@login_required
def create_checkin(request):
    if request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    # show default questions in UI
    questions = Question.objects.filter(is_default=True)

    if request.method == "POST":
        period = request.POST.get("period")
        deadline = request.POST.get("deadline")

        # 1️⃣ Create check-in form
        checkin = CheckInForm.objects.create(
            title=f"{period.capitalize()} Check-In",
            period=period,
            deadline=deadline,
            created_by=request.user
        )

        # 2️⃣ Attach selected DEFAULT questions
        selected_questions = request.POST.getlist("questions")
        for q_id in selected_questions:
            CheckInFormQuestion.objects.get_or_create(
                checkin_form=checkin,
                question_id=q_id
            )

        # 3️⃣ Handle CUSTOM questions
        for text in request.POST.getlist("custom_questions[]"):
            text = text.strip()
            if text:
                q = Question.objects.create(
                    question_text=text,
                    is_default=False,
                    created_by=request.user
                )
                CheckInFormQuestion.objects.create(
                    checkin_form=checkin,
                    question=q
                )

        # 4️⃣ Assign check-in to all employees
        for emp in User.objects.filter(role="EMPLOYEE"):
            CheckInAssignment.objects.create(
                checkin_form=checkin,
                employee=emp,
                status="PENDING"
            )

        return redirect("admin_checkins_list")

    return render(
        request,
        "checkins/create_checkin.html",
        {"questions": questions}
    )

# -------------------------------
# EMPLOYEE: CHECK-IN LIST
# -------------------------------
@login_required
def employee_checkins(request):
    assignments = CheckInAssignment.objects.filter(employee=request.user)
    return render(request, "checkins/employee_checkins.html", {"assignments": assignments})


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

    questions = (
        CheckInFormQuestion.objects
        .filter(checkin_form=assignment.checkin_form)
        .select_related("question")
    )

    if request.method == "POST" and assignment.status == "PENDING":
        for fq in questions:
            CheckInAnswer.objects.update_or_create(
                assignment=assignment,
                question=fq.question,
                defaults={
                    "employee": request.user,
                    "answer_text": request.POST.get(
                        f"question_{fq.question.id}", ""
                    )
                }
            )

        assignment.status = "SUBMITTED"
        assignment.submitted_at = timezone.now()
        assignment.save()

        return redirect("employee_checkins")

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
        }
    )


# -------------------------------
# ADMIN: CHECK-INS LIST (MODULE 6)
# -------------------------------
@login_required
def admin_checkins_list(request):
    if request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    assignments = (
        CheckInAssignment.objects
        .select_related("employee", "checkin_form")
        .order_by("-assigned_at")
    )

    total_submitted = assignments.filter(status="SUBMITTED").count()
    pending_review = assignments.filter(
        status="SUBMITTED",
        review_status="PENDING"
    ).count()
    reviewed = assignments.filter(
        status="SUBMITTED",
        review_status="REVIEWED"
    ).count()

    return render(
        request,
        "checkins/admin/admin_checkins_list.html",
        {
            "assignments": assignments,
            "total_submitted": total_submitted,
            "pending_review": pending_review,
            "reviewed": reviewed,
        }
    )






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
        assignment.status = "REVIEWED"
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

