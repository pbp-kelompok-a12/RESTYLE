import json
import time
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from closet.models import MANUAL_STATUS_CATEGORIES
from mixmatch.models import Outfit, SLOTS
from .models import DailyPlan, PlannerSettings
from .services import sync_item_statuses, washing_item_ids

LOGIN_URL = "/login/"
WEEKDAYS = [(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")]
WEATHER_COLORS = {
    "Hot": "sunny", "Stormy": "stormy", "Cool": "cloudy", "Moderate": "moderate",
    "Rainy": "rainy", "Drizzle": "drizzle", "Thunderstorm": "thunderstorm", "Flexible": "flexible",
}
WEATHER_CODES = {
    0: ("Sunny", "Hot", "sunny"), 1: ("Mostly sunny", "Hot", "sunny"),
    2: ("Partly cloudy", "Moderate", "cloudy"), 3: ("Cloudy", "Cool", "cloudy"),
    45: ("Foggy", "Cool", "cloudy"), 48: ("Foggy", "Cool", "cloudy"),
    51: ("Drizzle", "Drizzle", "drizzle"), 53: ("Drizzle", "Drizzle", "drizzle"), 55: ("Drizzle", "Drizzle", "drizzle"),
    56: ("Freezing drizzle", "Cool", "drizzle"), 57: ("Freezing drizzle", "Cool", "drizzle"),
    61: ("Rainy", "Rainy", "rainy"), 63: ("Rainy", "Rainy", "rainy"), 65: ("Heavy rain", "Rainy", "rainy"),
    66: ("Freezing rain", "Cool", "rainy"), 67: ("Freezing rain", "Cool", "rainy"),
    71: ("Snowy", "Cool", "snowy"), 73: ("Snowy", "Cool", "snowy"), 75: ("Heavy snow", "Cool", "snowy"), 77: ("Snow grains", "Cool", "snowy"),
    80: ("Rain showers", "Rainy", "rainy"), 81: ("Rain showers", "Rainy", "rainy"), 82: ("Heavy showers", "Rainy", "rainy"),
    85: ("Snow showers", "Cool", "snowy"), 86: ("Heavy snow showers", "Cool", "snowy"),
    95: ("Thunderstorm", "Thunderstorm", "thunderstorm"),
    96: ("Thunderstorm", "Thunderstorm", "thunderstorm"), 99: ("Thunderstorm", "Thunderstorm", "thunderstorm"),
}


def get_monday(d):
    return d - timedelta(days=d.weekday())


def get_settings(user):
    pref, _ = PlannerSettings.objects.get_or_create(user=user)
    return pref


def latest_laundry_day(on_date, weekdays):
    """Most recent selected laundry day, including on_date itself."""
    candidates = [on_date - timedelta(days=i) for i in range(7) if (on_date - timedelta(days=i)).weekday() in weekdays]
    return max(candidates) if candidates else None


def item_is_washing(item, user, target_date, current_plan=None, weekdays=None, laundry_time_days=None):
    preferences = get_settings(user) if weekdays is None or laundry_time_days is None else None
    weekdays = weekdays if weekdays is not None else preferences.laundry_weekdays
    laundry_time_days = laundry_time_days if laundry_time_days is not None else preferences.laundry_time_days
    return item.pk in washing_item_ids(
        user, target_date, weekdays, laundry_time_days, exclude_plan=current_plan
    )


def outfit_status(outfit, user, target_date, current_plan=None, weekdays=None, laundry_time_days=None):
    pieces = []
    for slot in SLOTS:
        if slot == "accessories":
            pieces.extend(outfit.accessories.all())
        else:
            piece = getattr(outfit, slot)
            if piece is not None:
                pieces.append(piece)
    if any(
        piece.category in MANUAL_STATUS_CATEGORIES and piece.status == "washing"
        for piece in pieces
    ):
        return "washing"
    scheduled_pieces = [
        piece for piece in pieces if piece.category not in MANUAL_STATUS_CATEGORIES
    ]
    if weekdays is None or laundry_time_days is None:
        preferences = get_settings(user)
        weekdays = weekdays if weekdays is not None else preferences.laundry_weekdays
        laundry_time_days = laundry_time_days if laundry_time_days is not None else preferences.laundry_time_days
    washing_ids = washing_item_ids(
        user, target_date, weekdays, laundry_time_days, exclude_plan=current_plan
    )
    return "washing" if any(piece.pk in washing_ids for piece in scheduled_pieces) else "ready"


def serialize_outfit(outfit, user, target_date, current_plan, weekdays, laundry_time_days):
    weather = outfit_weather(outfit)
    status = outfit_status(outfit, user, target_date, current_plan, weekdays, laundry_time_days)
    selected = bool(current_plan and current_plan.outfit_id == outfit.pk)
    return {
        "id": outfit.pk, "name": outfit.name, "tags": outfit.tags or [],
        "weather": weather or "Flexible", "weather_key": weather,
        "weather_class": WEATHER_COLORS.get(weather, "flexible" if not weather else "unknown"),
        "status": status, "status_label": "In The Wash" if status == "washing" else "Ready", "selected": selected,
        "html": render_to_string("mixmatch/_outfit_card.html", {
            "o": outfit, "selectable": True, "status": status, "weather": weather,
            "weather_class": WEATHER_COLORS.get(weather, "flexible" if not weather else "unknown"), "selected": selected, "show_delete": False,
        }),
    }


def outfit_weather(outfit):
    """Use the first weather preference shared by its pieces."""
    preferences = [set(item.weather or []) for item in outfit.pieces]
    if not preferences:
        return ""
    common = set.intersection(*preferences) if preferences else set()
    from closet.models import WEATHER_OPTIONS
    return next((weather for weather in WEATHER_OPTIONS if weather in common), "")


def build_week_slots(user, monday, weekdays, laundry_time_days):
    plans = {
        plan.date: plan
        for plan in DailyPlan.objects.filter(user=user, date__range=(monday, monday + timedelta(days=6)))
        .select_related(
            "outfit",
            *("outfit__" + slot for slot in SLOTS if slot != "accessories")
        ).prefetch_related("outfit__accessories")
    }
    slots = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        plan = plans.get(day)
        status = outfit_status(plan.outfit, user, day, plan, weekdays, laundry_time_days) if plan else "ready"
        visible = bool(plan and status == "ready")
        card_html = ""
        if visible:
            weather = outfit_weather(plan.outfit)
            card_html = render_to_string("mixmatch/_outfit_card.html", {
                "o": plan.outfit, "planner_day": True, "planner_date": day,
                "status": status, "weather": weather,
                "weather_class": WEATHER_COLORS.get(weather, "flexible" if not weather else "unknown"), "show_delete": False,
            })
        slots.append({"date": day, "plan": plan, "visible": visible, "html": card_html})
    return slots


@login_required(login_url=LOGIN_URL)
def show_planner(request):
    sync_item_statuses(request.user)
    raw = request.GET.get("week")
    try:
        ref = date.fromisoformat(raw) if raw else date.today()
    except ValueError:
        ref = date.today()

    monday = get_monday(ref)
    pref = get_settings(request.user)
    days = build_week_slots(request.user, monday, pref.laundry_weekdays, pref.laundry_time_days)

    week_options = []
    for i in range(-4, 9):
        m = monday + timedelta(weeks=i)
        s = m + timedelta(days=6)
        week_options.append({"value": m.isoformat(), "label": f"{m:%B} {m.day} - {s:%B} {s.day}", "selected": m == monday})

    context = {
        "days": days, "week_options": week_options,
        "prev_week": (monday - timedelta(weeks=1)).isoformat(), "next_week": (monday + timedelta(weeks=1)).isoformat(),
        "weekday_choices": WEEKDAYS, "laundry_weekdays": pref.laundry_weekdays,
        "laundry_time_days": pref.laundry_time_days,
    }
    return render(request, "planner.html", context)


def fetch_current_weather(latitude, longitude):
    query = urlencode({"latitude": latitude, "longitude": longitude, "current": "temperature_2m,weather_code", "timezone": "auto"})
    with urlopen(f"https://api.open-meteo.com/v1/forecast?{query}", timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    code = payload["current"]["weather_code"]
    if code not in WEATHER_CODES:
        raise ValueError("Unknown weather code")
    label, category, theme = WEATHER_CODES[code]
    temperature = payload["current"].get("temperature_2m")
    if temperature is None:
        raise ValueError("Temperature unavailable")
    return {"condition": label, "category": category, "theme": theme, "temperature": round(float(temperature))}


def reverse_geocode(latitude, longitude):
    cache_key = f"restyle_location_{round(float(latitude), 4)}_{round(float(longitude), 4)}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    # Nominatim asks applications to identify themselves and keep usage modest.
    # Cache location labels and rate-limit cache misses across requests.
    if not cache.add("restyle_nominatim_rate_limit", True, timeout=1):
        return "Location unavailable"
    query = urlencode({"lat": latitude, "lon": longitude, "format": "jsonv2", "zoom": 10, "addressdetails": 1})
    request = Request(
        f"https://nominatim.openstreetmap.org/reverse?{query}",
        headers={"User-Agent": "RE-STYLE planner location lookup/1.0"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        address = payload.get("address", {})
        locality = next((address[key] for key in ("city", "town", "village", "municipality", "suburb", "county") if address.get(key)), "")
        region = address.get("state", "")
        country = address.get("country", "")
        name = ", ".join(dict.fromkeys(part for part in (locality, region or country) if part))
        name = name or payload.get("name") or "Current location"
    except (URLError, TimeoutError, ValueError, KeyError, OSError):
        name = "Current location"
    cache.set(cache_key, name, timeout=60 * 60 * 24 * 7)
    return name


@login_required(login_url=LOGIN_URL)
@require_GET
def outfit_options(request):
    sync_item_statuses(request.user)
    day = parse_date(request.GET.get("date", ""))
    if not day:
        return JsonResponse({"error": "Invalid planner date."}, status=400)
    plan = DailyPlan.objects.filter(user=request.user, date=day).first()
    prefs = get_settings(request.user)
    outfits = list(
        Outfit.objects.filter(user=request.user)
        .select_related(*(slot for slot in SLOTS if slot != "accessories"))
        .prefetch_related("accessories")
    )
    cards = [serialize_outfit(
        o, request.user, day, plan, prefs.laundry_weekdays, prefs.laundry_time_days
    ) for o in outfits]
    return JsonResponse({"date": day.isoformat(), "outfits": cards, "selected_id": plan.outfit_id if plan else None})


@login_required(login_url=LOGIN_URL)
@require_GET
def current_weather(request):
    try:
        latitude = float(request.GET.get("latitude", ""))
        longitude = float(request.GET.get("longitude", ""))
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("Coordinates are out of range")
    except (TypeError, ValueError):
        return JsonResponse({"error": "Valid location coordinates are required."}, status=400)
    location = reverse_geocode(latitude, longitude)
    try:
        weather = fetch_current_weather(latitude, longitude)
    except (URLError, TimeoutError, ValueError, KeyError, IndexError, OSError):
        return JsonResponse({"error": "Weather is unavailable right now.", "location": location}, status=503)
    return JsonResponse({
        **weather, "location": location, "latitude": latitude, "longitude": longitude,
        "timestamp": int(time.time()),
    })


@login_required(login_url=LOGIN_URL)
@require_GET
def forecast_weather(request):
    day = parse_date(request.GET.get("date", ""))
    try:
        latitude = float(request.GET.get("latitude", ""))
        longitude = float(request.GET.get("longitude", ""))
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("Coordinates are out of range")
    except (TypeError, ValueError):
        return JsonResponse({"error": "Valid location coordinates are required."}, status=400)
    if not day:
        return JsonResponse({"error": "Invalid forecast date."}, status=400)

    today = timezone.localdate()
    days_ahead = (day - today).days
    if days_ahead < 0 or days_ahead > 16:
        return JsonResponse({"no_data": True, "date": day.isoformat()})

    cache_key = f"planner_forecast_{round(latitude, 5)}_{round(longitude, 5)}_{day.isoformat()}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    query = urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "start_date": day.isoformat(),
        "end_date": day.isoformat(),
        "timezone": "auto",
    })
    try:
        with urlopen(f"https://api.open-meteo.com/v1/forecast?{query}", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        daily = payload.get("daily", {})
        dates = daily.get("time", [])
        if day.isoformat() not in dates:
            return JsonResponse({"no_data": True, "date": day.isoformat()})
        index = dates.index(day.isoformat())
        codes = daily.get("weather_code", [])
        highs = daily.get("temperature_2m_max", [])
        lows = daily.get("temperature_2m_min", [])
        if index >= len(codes) or index >= len(highs) or index >= len(lows):
            return JsonResponse({"no_data": True, "date": day.isoformat()})
        code, high, low = codes[index], highs[index], lows[index]
        if code not in WEATHER_CODES or high is None or low is None:
            return JsonResponse({"no_data": True, "date": day.isoformat()})
        condition, category, theme = WEATHER_CODES[code]
        result = {
            "no_data": False,
            "date": day.isoformat(),
            "condition": condition,
            "category": category,
            "theme": theme,
            "temperature": round((float(high) + float(low)) / 2),
            "temperature_label": "daily average",
        }
        cache.set(cache_key, result, timeout=15 * 60)
        return JsonResponse(result)
    except HTTPError as error:
        if error.code == 400:
            return JsonResponse({"no_data": True, "date": day.isoformat()})
        return JsonResponse({"error": "Weather forecast is unavailable right now."}, status=503)
    except (URLError, TimeoutError, ValueError, KeyError, IndexError, OSError):
        return JsonResponse({"error": "Weather forecast is unavailable right now."}, status=503)


@login_required(login_url=LOGIN_URL)
@require_GET
def search_locations(request):
    query = request.GET.get("name", "").strip()
    if len(query) < 2:
        return JsonResponse({"locations": []})
    params = urlencode({"name": query, "count": 5, "language": "en", "format": "json"})
    try:
        with urlopen(f"https://geocoding-api.open-meteo.com/v1/search?{params}", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        locations = []
        for place in payload.get("results", [])[:5]:
            latitude = place.get("latitude")
            longitude = place.get("longitude")
            if latitude is None or longitude is None:
                continue
            name = place.get("name", "")
            region = place.get("admin1", "")
            country = place.get("country", "")
            label = ", ".join(dict.fromkeys(value for value in (name, region, country) if value))
            locations.append({"name": label or name, "latitude": latitude, "longitude": longitude})
        return JsonResponse({"locations": locations})
    except (URLError, TimeoutError, ValueError, OSError):
        return JsonResponse({"error": "Location search is unavailable right now."}, status=503)


@login_required(login_url=LOGIN_URL)
@require_GET
def week_state(request):
    sync_item_statuses(request.user)
    week = parse_date(request.GET.get("week", ""))
    if not week:
        return JsonResponse({"error": "Invalid planner week."}, status=400)
    monday = get_monday(week)
    pref = get_settings(request.user)
    slots = build_week_slots(request.user, monday, pref.laundry_weekdays, pref.laundry_time_days)
    return JsonResponse({"slots": [
        {"date": slot["date"].isoformat(), "plan_id": slot["plan"].outfit_id if slot["plan"] else None,
         "visible": slot["visible"], "html": slot["html"]}
        for slot in slots
    ]})


@login_required(login_url=LOGIN_URL)
@require_POST
def save_plan(request):
    try:
        data = json.loads(request.body)
        day = parse_date(data.get("date", ""))
        outfit_id = int(data.get("outfit_id"))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid plan data."}, status=400)

    if not day:
        return JsonResponse({"error": "Invalid planner date."}, status=400)
    outfit = get_object_or_404(
        Outfit.objects.filter(user=request.user)
        .select_related(*(slot for slot in SLOTS if slot != "accessories"))
        .prefetch_related("accessories"),
        pk=outfit_id,
    )
    existing = DailyPlan.objects.filter(user=request.user, date=day).first()
    prefs = get_settings(request.user)

    if day < timezone.localdate():
        return JsonResponse({"error": "Invalid planner date"}, status=400)
    if outfit_status(
        outfit, request.user, day, existing, prefs.laundry_weekdays, prefs.laundry_time_days
    ) == "washing":
        return JsonResponse({"error": "This outfit contains clothing that is in the wash."}, status=409)
    DailyPlan.objects.update_or_create(user=request.user, date=day, defaults={"outfit": outfit})
    sync_item_statuses(request.user)
    return JsonResponse({"ok": True, "outfit": outfit.name, "outfit_id": outfit.pk, "date": day.isoformat()})


@login_required(login_url=LOGIN_URL)
@require_POST
def clear_plan(request):
    try:
        data = json.loads(request.body)
        day = parse_date(data.get("date", ""))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid planner date."}, status=400)
    if not day:
        return JsonResponse({"error": "Invalid planner date."}, status=400)
    DailyPlan.objects.filter(user=request.user, date=day).delete()
    sync_item_statuses(request.user)
    return JsonResponse({"ok": True, "date": day.isoformat()})


@login_required(login_url=LOGIN_URL)
@require_POST
def save_laundry_days(request):
    values = request.POST.getlist("laundry_weekdays")
    try:
        weekdays = sorted({int(value) for value in values})
        laundry_time_days = int(request.POST.get("laundry_time_days", ""))
        if not weekdays or any(value not in range(7) for value in weekdays):
            raise ValueError
        if not 1 <= laundry_time_days <= 31:
            raise ValueError
    except ValueError:
        return JsonResponse({"error": "Choose valid laundry weekdays and duration."}, status=400)
    pref = get_settings(request.user)
    pref.laundry_weekdays = weekdays
    pref.laundry_time_days = laundry_time_days
    pref.save(update_fields=["laundry_weekdays", "laundry_time_days"])
    sync_item_statuses(request.user)
    return JsonResponse({"ok": True})
