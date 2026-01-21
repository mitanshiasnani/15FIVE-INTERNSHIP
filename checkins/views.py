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
from django.http import HttpResponse
from checkins.models import CheckInAssignment
from checkins.services.slack import (
    send_checkin_assigned_dm,
    send_admin_all_submitted_dm,
)
from checkins.services.slack import send_checkin_reviewed_dm

# -------------------------------
# ADMIN: CREATE CHECK-IN
# -------------------------------
from datetime import timedelta
from checkins.services.slack import send_checkin_assigned_dm


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import (
    CheckInForm,
    CheckInFormQuestion,
    CheckInAssignment,
    Question
)
from django.contrib.auth import get_user_model

User = get_user_model()

# checkins/views.py

from datetime import timedelta
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import (
    CheckInForm,
    Question,
    CheckInFormQuestion,
    CheckInAssignment,
)
from django.contrib.auth import get_user_model

User = get_user_model()


from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import CheckInForm, CheckInFormQuestion, CheckInAssignment, Question
from django.contrib.auth import get_user_model
from .services.slack import send_checkin_assigned_dm

User = get_user_model()


from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

from .models import (
    CheckInForm,
    CheckInAssignment,
    CheckInFormQuestion,
    Question,
)
from .services.slack import send_checkin_assigned_dm

User = get_user_model()

from datetime import timedelta
from calendar import monthrange
from django.utils import timezone

@login_required
def create_checkin(request):
    if request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    questions = Question.objects.filter(is_default=True)

    if request.method == "POST":
        period = request.POST.get("period")
        start_date = request.POST.get("start_date")

        start_date = timezone.datetime.strptime(
            start_date, "%Y-%m-%d"
        ).date()

        # ✅ AUTO-CALCULATE END DATE
        if period == "WEEKLY":
            end_date = start_date + timedelta(days=6)

        elif period == "MONTHLY":
            last_day = monthrange(start_date.year, start_date.month)[1]
            end_date = start_date.replace(day=last_day)

        selected_questions = request.POST.getlist("questions")
        custom_questions = request.POST.getlist("custom_questions[]")

        if not selected_questions and not custom_questions:
            return render(
                request,
                "checkins/create_checkin.html",
                {
                    "questions": questions,
                    "error": "Please select or add at least one question."
                }
            )

        # ✅ CREATE CHECK-IN FORM
        checkin = CheckInForm.objects.create(
            title=f"{period.capitalize()} Check-In",
            period=period,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user
        )

        # ✅ CLEAR SAFELY
        CheckInFormQuestion.objects.filter(
            checkin_form=checkin
        ).delete()

        # ✅ ADD SELECTED QUESTIONS
        for q_id in set(selected_questions):
            CheckInFormQuestion.objects.create(
                checkin_form=checkin,
                question_id=q_id
            )

        # ✅ ADD CUSTOM QUESTIONS
        for text in custom_questions:
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

        # ✅ CREATE ASSIGNMENTS + SLACK DM
        for emp in User.objects.filter(role="EMPLOYEE"):
            assignment = CheckInAssignment.objects.create(
                checkin_form=checkin,
                employee=emp,
                status="PENDING",
                review_status="PENDING"
            )

            profile = getattr(emp, "employeeprofile", None)
            if profile and profile.slack_user_id:
                send_checkin_assigned_dm(
                    slack_user_id=profile.slack_user_id,
                    title=checkin.title,
                    start_date=start_date,
                    end_date=end_date
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
    return render(
        request,
        "core/employee_checkins.html",
        {"assignments": assignments}
    )


# -------------------------------
# EMPLOYEE: CHECK-IN FORM
# -------------------------------
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from checkins.models import (
    CheckInAssignment,
    CheckInFormQuestion,
    CheckInAnswer,
)
from checkins.services.slack import send_admin_all_submitted_dm


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import (
    CheckInAssignment,
    CheckInFormQuestion,
    CheckInAnswer,
)
from .services.slack import send_admin_all_submitted_dm


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

    # 🔒 Block edits if submitted or expired
    is_readonly = assignment.status == "SUBMITTED" or is_expired

    if request.method == "POST":
        if is_readonly:
            return redirect("employee_dashboard")

        action = request.POST.get("action")

        has_any_answer = False

        # ✅ Save / update answers
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

        # 📝 SAVE DRAFT → PARTIAL
        if action == "draft":
            if has_any_answer and assignment.status != "SUBMITTED":
                assignment.status = "PARTIAL"
                assignment.save()

        # 🚀 SUBMIT → SUBMITTED
        elif action == "submit":
            assignment.status = "SUBMITTED"
            assignment.submitted_at = timezone.now()
            assignment.save()

            # 🔔 Notify admin ONLY when all submitted
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

    # 📥 Existing answers (GET)
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
# -------------------------------
# ADMIN: CHECK-INS HISTORY (FORM LEVEL)
# -------------------------------
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import CheckInForm, CheckInAssignment


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
        # 1️⃣ Mark as reviewed ONLY if not already reviewed
        if assignment.review_status != "REVIEWED":
            assignment.review_status = "REVIEWED"
            assignment.reviewed_at = timezone.now()
            assignment.save()

            # 2️⃣ Slack DM to employee
            profile = getattr(assignment.employee, "employeeprofile", None)
            if profile and profile.slack_user_id:
                send_checkin_reviewed_dm(
                    slack_user_id=profile.slack_user_id,
                    title=assignment.checkin_form.title
                )

            # 3️⃣ Email notification (existing behavior)
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



@login_required
def admin_checkin_form_detail(request, form_id):
    if request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    form = get_object_or_404(CheckInForm, id=form_id)

    assignments = (
        CheckInAssignment.objects
        .filter(checkin_form=form)
        .select_related("employee")
    )

    return render(
        request,
        "core/admin_employee_checkins.html",
        {
            "form": form,
            "assignments": assignments,
        }
    )




@login_required
def admin_employee_checkins(request, employee_id):
    if request.user.role != "ADMIN":
        return redirect("employee_dashboard")

    employee = get_object_or_404(User, id=employee_id, role="EMPLOYEE")

    assignments = (
        CheckInAssignment.objects
        .filter(employee=employee)   # 🔥 THIS IS WHY DATA EXISTS
        .select_related("checkin_form")
        .order_by("-assigned_at")
    )

    return render(
        request,
        "core/admin_employee_checkins.html",
        {
            "employee": employee,
            "assignments": assignments,  # 🔥 TEMPLATE EXPECTS THIS
        }
    )
















