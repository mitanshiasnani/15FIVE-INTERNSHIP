from django.db.models import Count, Q
from django.utils import timezone
from collections import defaultdict
from datetime import timedelta

# ─────────────────────────────────────────────
# SENTIMENT — uses TextBlob (pip install textblob)
# Falls back gracefully if not installed
# ─────────────────────────────────────────────
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False


def get_sentiment(text):
    """
    Returns: 'positive', 'neutral', or 'negative'
    Polarity: -1.0 (very negative) to +1.0 (very positive)
    """
    if not TEXTBLOB_AVAILABLE or not text or not text.strip():
        return "neutral"

    polarity = TextBlob(text).sentiment.polarity

    if polarity >= 0.1:
        return "positive"
    elif polarity <= -0.1:
        return "negative"
    else:
        return "neutral"


def get_sentiment_score(text):
    """Returns raw polarity score -1.0 to 1.0"""
    if not TEXTBLOB_AVAILABLE or not text or not text.strip():
        return 0.0
    return round(TextBlob(text).sentiment.polarity, 3)


# ─────────────────────────────────────────────
# COMPLETION RATE ANALYTICS
# ─────────────────────────────────────────────
def get_completion_trend(weeks=8):
    """
    Returns weekly completion rates for the last N weeks.
    Each entry: { 'week_label': 'Week of Apr 7', 'rate': 82.5 }
    """
    from checkins.models import CheckInAssignment

    today = timezone.now().date()
    results = []

    for i in range(weeks - 1, -1, -1):
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)

        assignments = CheckInAssignment.objects.filter(
            assigned_at__date__gte=week_start,
            assigned_at__date__lte=week_end,
        )

        total = assignments.count()
        submitted = assignments.filter(status="SUBMITTED").count()

        rate = round((submitted / total * 100), 1) if total > 0 else 0

        results.append({
            "week_label": f"{week_start.strftime('%b %d')}",
            "total": total,
            "submitted": submitted,
            "rate": rate,
        })

    return results


def get_employee_completion_rates():
    """
    Returns per-employee stats for leaderboard/table.
    Each entry: { 'email': ..., 'total': ..., 'submitted': ..., 'rate': ... }
    """
    from checkins.models import CheckInAssignment
    from accounts.models import User

    employees = User.objects.filter(role="EMPLOYEE", is_active=True)
    results = []

    for emp in employees:
        assignments = CheckInAssignment.objects.filter(employee=emp)
        total = assignments.count()
        submitted = assignments.filter(status="SUBMITTED").count()
        rate = round((submitted / total * 100), 1) if total > 0 else 0

        # Get display name
        try:
            name = emp.employeeprofile.full_name or emp.email.split("@")[0]
        except Exception:
            name = emp.email.split("@")[0]

        results.append({
            "email": emp.email,
            "name": name,
            "total": total,
            "submitted": submitted,
            "pending": total - submitted,
            "rate": rate,
        })

    # Sort by rate descending
    results.sort(key=lambda x: x["rate"], reverse=True)
    return results


# ─────────────────────────────────────────────
# SENTIMENT ANALYTICS
# ─────────────────────────────────────────────
def get_sentiment_trend(weeks=8):
    """
    Returns weekly average sentiment scores.
    Each entry: { 'week_label': 'Apr 7', 'positive': N, 'neutral': N, 'negative': N }
    """
    from checkins.models import CheckInAnswer

    today = timezone.now().date()
    results = []

    for i in range(weeks - 1, -1, -1):
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)

        answers = CheckInAnswer.objects.filter(
            updated_at__date__gte=week_start,
            updated_at__date__lte=week_end,
            answer_text__isnull=False,
        ).exclude(answer_text="")

        counts = {"positive": 0, "neutral": 0, "negative": 0}

        for answer in answers:
            sentiment = get_sentiment(answer.answer_text)
            counts[sentiment] += 1

        results.append({
            "week_label": week_start.strftime("%b %d"),
            **counts,
        })

    return results


def get_employee_sentiment_summary():
    """
    Per-employee mood summary across all submitted answers.
    Returns list of { name, email, positive, neutral, negative, dominant_mood, avg_score }
    """
    from checkins.models import CheckInAnswer, CheckInAssignment
    from accounts.models import User

    employees = User.objects.filter(role="EMPLOYEE", is_active=True)
    results = []

    for emp in employees:
        answers = CheckInAnswer.objects.filter(
            employee=emp,
            assignment__status="SUBMITTED",
        ).exclude(answer_text="")

        counts = {"positive": 0, "neutral": 0, "negative": 0}
        scores = []

        for answer in answers:
            sentiment = get_sentiment(answer.answer_text)
            counts[sentiment] += 1
            scores.append(get_sentiment_score(answer.answer_text))

        total_answers = sum(counts.values())
        if total_answers == 0:
            continue

        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        dominant = max(counts, key=counts.get)

        try:
            name = emp.employeeprofile.full_name or emp.email.split("@")[0]
        except Exception:
            name = emp.email.split("@")[0]

        results.append({
            "name": name,
            "email": emp.email,
            "positive": counts["positive"],
            "neutral": counts["neutral"],
            "negative": counts["negative"],
            "total": total_answers,
            "dominant_mood": dominant,
            "avg_score": avg_score,
        })

    results.sort(key=lambda x: x["avg_score"], reverse=True)
    return results


# ─────────────────────────────────────────────
# SUMMARY STATS FOR DASHBOARD HEADER
# ─────────────────────────────────────────────
def get_summary_stats():
    from checkins.models import CheckInAssignment, CheckInAnswer
    from accounts.models import User

    total_employees = User.objects.filter(role="EMPLOYEE", is_active=True).count()
    total_assignments = CheckInAssignment.objects.count()
    total_submitted = CheckInAssignment.objects.filter(status="SUBMITTED").count()
    overall_rate = round((total_submitted / total_assignments * 100), 1) if total_assignments > 0 else 0

    # Sentiment breakdown across ALL answers
    all_answers = CheckInAnswer.objects.filter(
        assignment__status="SUBMITTED"
    ).exclude(answer_text="")

    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for a in all_answers:
        sentiment_counts[get_sentiment(a.answer_text)] += 1

    total_answers = sum(sentiment_counts.values())
    positive_pct = round(sentiment_counts["positive"] / total_answers * 100) if total_answers else 0

    return {
        "total_employees": total_employees,
        "total_assignments": total_assignments,
        "total_submitted": total_submitted,
        "overall_completion_rate": overall_rate,
        "sentiment_counts": sentiment_counts,
        "positive_pct": positive_pct,
        "textblob_available": TEXTBLOB_AVAILABLE,
    }
