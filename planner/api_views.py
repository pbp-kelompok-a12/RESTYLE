from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
import json

from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mixmatch.models import Outfit, SLOTS
from .models import DailyPlan, PlannerSettings
from .services import sync_item_statuses
from .views import (WEATHER_CODES, build_week_slots, fetch_current_weather,
                    get_monday, get_settings, outfit_status, reverse_geocode)


def outfit_data(outfit):
    return {"id": outfit.pk, "name": outfit.name, "tags": outfit.tags or [],
            "items": {slot: ([item.pk for item in getattr(outfit, slot).all()]
                              if slot == "accessories" else
                              getattr(outfit, slot + "_id")) for slot in SLOTS}}


def plan_data(plan):
    return {"date": plan.date.isoformat(), "outfit": outfit_data(plan.outfit),
            "updated_at": plan.updated_at.isoformat()}


class PlannerWeekAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sync_item_statuses(request.user)
        ref = parse_date(request.query_params.get("week", ""))
        if not ref:
            return Response({"error": "week must be a valid YYYY-MM-DD date."}, status=400)
        monday = get_monday(ref)
        prefs = get_settings(request.user)
        plans = {p.date: p for p in DailyPlan.objects.filter(
            user=request.user, date__range=(monday, monday + timedelta(days=6))
        ).select_related("outfit").prefetch_related("outfit__accessories")}
        return Response({"week_start": monday.isoformat(), "slots": [
            {"date": slot["date"].isoformat(),
             "plan": plan_data(plans[slot["date"]]) if slot["date"] in plans else None,
             "status": outfit_status(plans[slot["date"]].outfit, request.user, slot["date"],
                                     plans[slot["date"]], prefs.laundry_weekdays,
                                     prefs.laundry_time_days) if slot["date"] in plans else "ready"}
            for slot in build_week_slots(request.user, monday, prefs.laundry_weekdays,
                                         prefs.laundry_time_days)]})


class PlannerOutfitsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        day = parse_date(request.query_params.get("date", ""))
        if not day:
            return Response({"error": "date must be a valid YYYY-MM-DD date."}, status=400)
        sync_item_statuses(request.user)
        plan = DailyPlan.objects.filter(user=request.user, date=day).first()
        prefs = get_settings(request.user)
        outfits = Outfit.objects.filter(user=request.user).prefetch_related("accessories")
        return Response({"date": day.isoformat(), "selected_id": plan.outfit_id if plan else None,
                         "outfits": [{**outfit_data(o), "status": outfit_status(
                             o, request.user, day, plan, prefs.laundry_weekdays,
                             prefs.laundry_time_days)} for o in outfits]})


class PlannerPlanAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = DailyPlan.objects.filter(user=request.user).select_related("outfit").prefetch_related("outfit__accessories")
        start, end = parse_date(request.query_params.get("start", "")), parse_date(request.query_params.get("end", ""))
        if start: qs = qs.filter(date__gte=start)
        if end: qs = qs.filter(date__lte=end)
        return Response([plan_data(p) for p in qs])

    def post(self, request):
        day = parse_date(request.data.get("date", ""))
        try: outfit_id = int(request.data.get("outfit_id"))
        except (ValueError, TypeError): outfit_id = None
        if not day or not outfit_id:
            return Response({"error": "Provide valid date and outfit_id."}, status=400)
        if day < timezone.localdate():
            return Response({"error": "Plans cannot be added in the past."}, status=400)
        outfit = Outfit.objects.filter(user=request.user, pk=outfit_id).prefetch_related("accessories").first()
        if not outfit:
            return Response({"error": "Outfit not found."}, status=404)
        existing = DailyPlan.objects.filter(user=request.user, date=day).first()
        prefs = get_settings(request.user)
        if outfit_status(outfit, request.user, day, existing, prefs.laundry_weekdays,
                         prefs.laundry_time_days) == "washing":
            return Response({"error": "This outfit contains clothing that is in the wash."}, status=409)
        plan, created = DailyPlan.objects.update_or_create(user=request.user, date=day,
                                                            defaults={"outfit": outfit})
        sync_item_statuses(request.user)
        return Response(plan_data(plan), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class PlannerPlanDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, day):
        parsed = parse_date(day)
        if not parsed:
            return Response({"error": "day must be a valid YYYY-MM-DD date."}, status=400)
        deleted, _ = DailyPlan.objects.filter(user=request.user, date=parsed).delete()
        sync_item_statuses(request.user)
        return Response(status=204 if deleted else 404)

    def put(self, request, day):
        data = request.data.copy()
        data["date"] = day
        request._full_data = data
        return PlannerPlanAPIView().post(request)

    patch = put


class PlannerSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        p = get_settings(request.user)
        return Response({"laundry_weekdays": p.laundry_weekdays,
                         "laundry_time_days": p.laundry_time_days})

    def patch(self, request):
        p = get_settings(request.user)
        days = request.data.get("laundry_weekdays", p.laundry_weekdays)
        duration = request.data.get("laundry_time_days", p.laundry_time_days)
        try:
            days = sorted(set(int(x) for x in days)); duration = int(duration)
            if not days or any(x not in range(7) for x in days) or not 1 <= duration <= 31: raise ValueError
        except (TypeError, ValueError):
            return Response({"error": "laundry_weekdays must contain 0-6 and duration 1-31."}, status=400)
        p.laundry_weekdays, p.laundry_time_days = days, duration
        p.save(update_fields=["laundry_weekdays", "laundry_time_days"])
        sync_item_statuses(request.user)
        return self.get(request)


class PlannerCurrentWeatherAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            lat, lon = float(request.query_params["latitude"]), float(request.query_params["longitude"])
            if not -90 <= lat <= 90 or not -180 <= lon <= 180: raise ValueError
            location = reverse_geocode(lat, lon)
            return Response({**fetch_current_weather(lat, lon), "location": location,
                             "latitude": lat, "longitude": lon})
        except (KeyError, ValueError, TypeError):
            return Response({"error": "Valid latitude and longitude are required."}, status=400)
        except (URLError, TimeoutError, OSError):
            return Response({"error": "Weather is unavailable right now."}, status=503)


class PlannerForecastAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        day = parse_date(request.query_params.get("date", ""))
        try:
            lat, lon = float(request.query_params["latitude"]), float(request.query_params["longitude"])
            if not day or not -90 <= lat <= 90 or not -180 <= lon <= 180: raise ValueError
        except (KeyError, ValueError, TypeError):
            return Response({"error": "Valid date, latitude and longitude are required."}, status=400)
        offset = (day - timezone.localdate()).days
        if not 0 <= offset <= 16: return Response({"no_data": True, "date": day.isoformat()})
        params = urlencode({"latitude": lat, "longitude": lon,
                            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                            "start_date": day.isoformat(), "end_date": day.isoformat(), "timezone": "auto"})
        try:
            with urlopen(f"https://api.open-meteo.com/v1/forecast?{params}", timeout=5) as response:
                daily = json.loads(response.read().decode()).get("daily", {})
            codes, highs, lows = daily.get("weather_code", []), daily.get("temperature_2m_max", []), daily.get("temperature_2m_min", [])
            if not codes or not highs or not lows or codes[0] not in WEATHER_CODES or highs[0] is None or lows[0] is None:
                return Response({"no_data": True, "date": day.isoformat()})
            condition, category, theme = WEATHER_CODES[codes[0]]
            result = {"no_data": False, "date": day.isoformat(), "condition": condition,
                      "category": category, "theme": theme,
                      "temperature": round((float(highs[0]) + float(lows[0])) / 2),
                      "temperature_label": "daily average"}
            return Response(result)
        except HTTPError as e:
            if e.code == 400: return Response({"no_data": True, "date": day.isoformat()})
            return Response({"error": "Weather forecast is unavailable right now."}, status=503)
        except (URLError, TimeoutError, OSError, ValueError, KeyError, IndexError):
            return Response({"error": "Weather forecast is unavailable right now."}, status=503)


class PlannerLocationSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        name = request.query_params.get("name", "").strip()
        if len(name) < 2: return Response({"locations": []})
        try:
            with urlopen("https://geocoding-api.open-meteo.com/v1/search?" + urlencode(
                    {"name": name, "count": 5, "language": "en", "format": "json"}), timeout=5) as response:
                data = json.loads(response.read().decode())
            results = [{"name": ", ".join(dict.fromkeys(x for x in
                        (p.get("name", ""), p.get("admin1", ""), p.get("country", "")) if x)),
                        "latitude": p["latitude"], "longitude": p["longitude"]}
                       for p in data.get("results", [])[:5] if "latitude" in p and "longitude" in p]
            return Response({"locations": results})
        except (URLError, TimeoutError, OSError, ValueError):
            return Response({"error": "Location search is unavailable right now."}, status=503)
