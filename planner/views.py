from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


LOGIN_URL = "/login/"
# Create your views here.
from datetime import date, timedelta
from django.shortcuts import render


def get_monday(d):
    return d - timedelta(days=d.weekday())  # weekday(): Senin = 0


def show_planner(request):
    raw = request.GET.get("week")
    try:
        ref = date.fromisoformat(raw) if raw else date.today()
    except ValueError:
        ref = date.today()

    today = date.today()
    monday = get_monday(ref)
    days = [
        {"date": monday + timedelta(days=i), "is_today": monday + timedelta(days=i) == today}
        for i in range(7)
    ]

    week_options = []
    for i in range(-4, 9):
        m = monday + timedelta(weeks=i)
        s = m + timedelta(days=6)
        week_options.append({
            "value": m.isoformat(),
            "label": f"{m:%B} {m.day} - {s:%B} {s.day}",
            "selected": m == monday,
        })

    context = {
        "days": days,
        "week_options": week_options,
        "prev_week": (monday - timedelta(weeks=1)).isoformat(),
        "next_week": (monday + timedelta(weeks=1)).isoformat(),
    }
    return render(request, "planner.html", context)