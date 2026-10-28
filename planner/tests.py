import json
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from closet.models import Item
from mixmatch.models import Outfit
from planner.models import DailyPlan, PlannerSettings
from planner.services import sync_item_statuses
from planner.views import get_monday, item_is_washing, latest_laundry_day


User = get_user_model()

PLAIN_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=PLAIN_STORAGES)
class PlannerTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("planner-user", password="pw12345!")
        self.other = User.objects.create_user("other-user", password="pw12345!")
        self.top = self.make_item(self.user, "Blue Shirt", "top")
        self.bottom = self.make_item(self.user, "Black Trousers", "bottom")
        self.other_top = self.make_item(self.other, "Other Shirt", "top")
        self.outfit = Outfit.objects.create(
            user=self.user, name="Campus Outfit", top=self.top, bottom=self.bottom
        )
        self.other_outfit = Outfit.objects.create(
            user=self.other, name="Other Outfit", top=self.other_top
        )
        self.client.login(username="planner-user", password="pw12345!")

    @staticmethod
    def make_item(user, name, category, status="ready", weather=None):
        return Item.objects.create(
            user=user,
            name=name,
            category=category,
            color="blue",
            status=status,
            weather=weather or [],
        )

    @staticmethod
    def json_body(**data):
        return json.dumps(data)

    def test_get_monday_returns_start_of_iso_week(self):
        self.assertEqual(get_monday(date(2026, 10, 28)), date(2026, 10, 26))

    def test_latest_laundry_day_includes_target_day(self):
        friday = date(2026, 10, 30)
        self.assertEqual(latest_laundry_day(friday, [friday.weekday()]), friday)

    def test_latest_laundry_day_returns_none_when_no_day_selected(self):
        self.assertIsNone(latest_laundry_day(date(2026, 10, 28), []))

    def test_planner_status_ignores_closet_item_status(self):
        item = self.make_item(self.user, "Wet Shirt", "top", status="washing")
        self.assertFalse(item_is_washing(item, self.user, date(2026, 10, 28), weekdays=[]))

    def test_recent_planned_wear_makes_item_unavailable_until_laundry_day(self):
        # Monday is the laundry day; a Tuesday wear is still recent on Wednesday.
        self.outfit.top = self.top
        self.outfit.save()
        tuesday = date(2026, 10, 27)
        wednesday = date(2026, 10, 28)
        DailyPlan.objects.create(user=self.user, date=tuesday, outfit=self.outfit)
        self.assertTrue(item_is_washing(self.top, self.user, wednesday, weekdays=[0]))

    def test_planned_wear_remains_washing_until_laundry_days_pass(self):
        thursday = date(2026, 10, 29)
        saturday = date(2026, 10, 31)
        DailyPlan.objects.create(user=self.user, date=thursday, outfit=self.outfit)
        self.assertTrue(item_is_washing(
            self.top, self.user, saturday, weekdays=[4], laundry_time_days=2
        ))
        self.assertFalse(item_is_washing(
            self.top, self.user, date(2026, 11, 1), weekdays=[4], laundry_time_days=2
        ))

    def test_closet_status_mirrors_today_planner_status(self):
        plan_day = date(2026, 10, 28)  # Wednesday
        washing_day = date(2026, 10, 29)  # Thursday
        ready_day = date(2026, 11, 2)  # Friday schedule + 3 days
        PlannerSettings.objects.create(
            user=self.user, laundry_weekdays=[4], laundry_time_days=3
        )
        DailyPlan.objects.create(user=self.user, date=plan_day, outfit=self.outfit)

        # Closet values do not decide Planner status; synchronization copies
        # the calculated status from the plan dates into the Closet fields.
        self.top.status = "ready"
        self.top.save(update_fields=["status"])
        sync_item_statuses(self.user, on_date=washing_day)
        self.top.refresh_from_db()
        self.bottom.refresh_from_db()
        self.assertEqual(self.top.status, "washing")
        self.assertEqual(self.bottom.status, "washing")

        sync_item_statuses(self.user, on_date=ready_day)
        self.top.refresh_from_db()
        self.bottom.refresh_from_db()
        self.assertEqual(self.top.status, "ready")
        self.assertEqual(self.bottom.status, "ready")

    def test_planner_page_shows_week_and_laundry_form(self):
        response = self.client.get(reverse("planner:show_planner"), {"week": "2026-10-28"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-week-start="2026-10-26"')
        self.assertContains(response, "Laundry days")
        self.assertContains(response, 'name="laundry_time_days"')
        self.assertContains(response, "Choose your Mix &amp; Match")

    def test_invalid_week_query_falls_back_to_current_week(self):
        response = self.client.get(reverse("planner:show_planner"), {"week": "not-a-date"})
        self.assertEqual(response.status_code, 200)
        current_monday = get_monday(date.today()).isoformat()
        self.assertContains(response, f'data-week-start="{current_monday}"')

    def test_outfit_options_returns_only_current_users_outfits(self):
        response = self.client.get(
            reverse("planner:outfit_options"), {"date": "2026-10-28"}
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["selected_id"], None)
        self.assertEqual([outfit["id"] for outfit in payload["outfits"]], [self.outfit.id])
        self.assertIn("Campus Outfit", payload["outfits"][0]["html"])

    def test_outfit_options_rejects_invalid_date(self):
        response = self.client.get(reverse("planner:outfit_options"), {"date": "invalid"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_save_plan_creates_and_then_replaces_daily_plan(self):
        other_item = self.make_item(self.user, "Green Dress", "dresses")
        replacement = Outfit.objects.create(
            user=self.user, name="Replacement", dresses=other_item
        )
        url = reverse("planner:save_plan")

        first = self.client.post(
            url,
            self.json_body(date="2026-10-28", outfit_id=self.outfit.id),
            content_type="application/json",
        )
        second = self.client.post(
            url,
            self.json_body(date="2026-10-28", outfit_id=replacement.id),
            content_type="application/json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(DailyPlan.objects.filter(user=self.user, date="2026-10-28").count(), 1)
        self.assertEqual(DailyPlan.objects.get(user=self.user, date="2026-10-28").outfit, replacement)

    def test_save_plan_rejects_invalid_json_and_date(self):
        url = reverse("planner:save_plan")
        bad_json = self.client.post(url, "{", content_type="application/json")
        bad_date = self.client.post(
            url,
            self.json_body(date="not-a-date", outfit_id=self.outfit.id),
            content_type="application/json",
        )
        self.assertEqual(bad_json.status_code, 400)
        self.assertEqual(bad_date.status_code, 400)

    def test_save_plan_does_not_allow_another_users_outfit(self):
        response = self.client.post(
            reverse("planner:save_plan"),
            self.json_body(date="2026-10-28", outfit_id=self.other_outfit.id),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(DailyPlan.objects.filter(user=self.user).exists())

    def test_save_plan_rejects_outfit_with_washing_item(self):
        PlannerSettings.objects.create(
            user=self.user, laundry_weekdays=[4], laundry_time_days=3
        )
        self.top.status = "washing"
        self.top.save(update_fields=["status"])
        DailyPlan.objects.create(
            user=self.user, date=date(2026, 10, 27), outfit=self.outfit
        )

        response = self.client.post(
            reverse("planner:save_plan"),
            self.json_body(date="2026-10-28", outfit_id=self.outfit.id),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("wash", response.json()["error"].lower())
        self.assertEqual(DailyPlan.objects.filter(user=self.user).count(), 1)

    def test_clear_plan_only_deletes_current_users_plan_for_given_date(self):
        DailyPlan.objects.create(user=self.user, date="2026-10-28", outfit=self.outfit)
        DailyPlan.objects.create(user=self.other, date="2026-10-28", outfit=self.other_outfit)

        response = self.client.post(
            reverse("planner:clear_plan"),
            self.json_body(date="2026-10-28"),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(DailyPlan.objects.filter(user=self.user, date="2026-10-28").exists())
        self.assertTrue(DailyPlan.objects.filter(user=self.other, date="2026-10-28").exists())

    def test_clear_plan_rejects_invalid_date(self):
        response = self.client.post(
            reverse("planner:clear_plan"),
            self.json_body(date="invalid"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_save_laundry_days_sorts_and_deduplicates_weekdays(self):
        response = self.client.post(
            reverse("planner:save_laundry_days"),
            {"laundry_weekdays": ["5", "1", "5"], "laundry_time_days": "3"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlannerSettings.objects.get(user=self.user).laundry_weekdays, [1, 5])
        self.assertEqual(PlannerSettings.objects.get(user=self.user).laundry_time_days, 3)

    def test_save_laundry_days_rejects_empty_or_out_of_range_values(self):
        url = reverse("planner:save_laundry_days")
        empty = self.client.post(url, {})
        invalid = self.client.post(url, {"laundry_weekdays": "7", "laundry_time_days": "2"})
        non_integer = self.client.post(url, {"laundry_weekdays": "monday", "laundry_time_days": "2"})
        invalid_duration = self.client.post(url, {"laundry_weekdays": "1", "laundry_time_days": "0"})
        self.assertEqual(empty.status_code, 400)
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(non_integer.status_code, 400)
        self.assertEqual(invalid_duration.status_code, 400)

    def test_week_state_returns_seven_slots_and_plan_state(self):
        monday = date(2026, 10, 26)
        DailyPlan.objects.create(user=self.user, date=monday, outfit=self.outfit)

        response = self.client.get(reverse("planner:week_state"), {"week": "2026-10-28"})

        self.assertEqual(response.status_code, 200)
        slots = response.json()["slots"]
        self.assertEqual(len(slots), 7)
        self.assertEqual(slots[0]["date"], monday.isoformat())
        self.assertEqual(slots[0]["plan_id"], self.outfit.id)
        self.assertTrue(slots[0]["visible"])

    def test_week_state_rejects_invalid_week(self):
        response = self.client.get(reverse("planner:week_state"), {"week": "invalid"})
        self.assertEqual(response.status_code, 400)

    def test_anonymous_user_is_redirected_from_planner_endpoints(self):
        self.client.logout()
        protected_gets = (
            ("planner:show_planner", {}),
            ("planner:outfit_options", {"date": "2026-10-28"}),
            ("planner:current_weather", {"latitude": "0", "longitude": "0"}),
            ("planner:forecast_weather", {
                "date": "2026-10-28", "latitude": "0", "longitude": "0"
            }),
            ("planner:search_locations", {"name": "Depok"}),
            ("planner:week_state", {"week": "2026-10-26"}),
        )
        for route_name, params in protected_gets:
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name), params)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login", response["Location"])

    def test_mutation_endpoints_require_post(self):
        for route_name in (
            "planner:save_plan",
            "planner:clear_plan",
            "planner:save_laundry_days",
        ):
            with self.subTest(route=route_name):
                self.assertEqual(self.client.get(reverse(route_name)).status_code, 405)

    def test_current_weather_rejects_invalid_coordinates(self):
        response = self.client.get(
            reverse("planner:current_weather"), {"latitude": "91", "longitude": "0"}
        )
        self.assertEqual(response.status_code, 400)

    @patch("planner.views.fetch_current_weather")
    @patch("planner.views.reverse_geocode", return_value="Depok")
    def test_current_weather_returns_normalized_provider_data(self, _reverse_geocode, fetch_weather):
        fetch_weather.return_value = {
            "condition": "Sunny", "category": "Hot", "theme": "sunny", "temperature": 30
        }
        response = self.client.get(
            reverse("planner:current_weather"), {"latitude": "-6.4", "longitude": "106.8"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["location"], "Depok")
        self.assertEqual(response.json()["theme"], "sunny")
        fetch_weather.assert_called_once_with(-6.4, 106.8)

    def test_forecast_rejects_invalid_coordinates_and_date(self):
        url = reverse("planner:forecast_weather")
        invalid_coordinates = self.client.get(
            url, {"date": "2026-10-28", "latitude": "91", "longitude": "0"}
        )
        invalid_date = self.client.get(
            url, {"date": "not-a-date", "latitude": "0", "longitude": "0"}
        )
        self.assertEqual(invalid_coordinates.status_code, 400)
        self.assertEqual(invalid_date.status_code, 400)

    def test_forecast_returns_no_data_for_past_date_without_provider_call(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        with patch("planner.views.urlopen") as urlopen:
            response = self.client.get(
                reverse("planner:forecast_weather"),
                {"date": yesterday.isoformat(), "latitude": "0", "longitude": "0"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["no_data"])
        urlopen.assert_not_called()

    def test_forecast_returns_no_data_beyond_supported_range(self):
        too_far = timezone.localdate() + timedelta(days=17)
        with patch("planner.views.urlopen") as urlopen:
            response = self.client.get(
                reverse("planner:forecast_weather"),
                {"date": too_far.isoformat(), "latitude": "0", "longitude": "0"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["no_data"])
        urlopen.assert_not_called()

    def test_forecast_returns_cached_result(self):
        forecast_date = timezone.localdate() + timedelta(days=1)
        cache_key = f"planner_forecast_0.0_0.0_{forecast_date.isoformat()}"
        expected = {"no_data": False, "date": forecast_date.isoformat(), "condition": "Sunny"}
        cache.set(cache_key, expected, timeout=900)

        with patch("planner.views.urlopen") as urlopen:
            response = self.client.get(
                reverse("planner:forecast_weather"),
                {"date": forecast_date.isoformat(), "latitude": "0", "longitude": "0"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        urlopen.assert_not_called()

    @patch("planner.views.urlopen")
    def test_forecast_maps_provider_data_and_caches_response(self, urlopen):
        forecast_date = timezone.localdate() + timedelta(days=1)
        provider_response = {
            "daily": {
                "time": [forecast_date.isoformat()],
                "weather_code": [0],
                "temperature_2m_max": [30.4],
                "temperature_2m_min": [20.4],
            }
        }
        response_context = urlopen.return_value.__enter__.return_value
        response_context.read.return_value = json.dumps(provider_response).encode("utf-8")

        response = self.client.get(
            reverse("planner:forecast_weather"),
            {"date": forecast_date.isoformat(), "latitude": "-6.4", "longitude": "106.8"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "no_data": False,
            "date": forecast_date.isoformat(),
            "condition": "Sunny",
            "category": "Hot",
            "theme": "sunny",
            "temperature": 25,
            "temperature_label": "daily average",
        })
        urlopen.assert_called_once()

    def test_location_search_returns_empty_for_short_query(self):
        with patch("planner.views.urlopen") as urlopen:
            response = self.client.get(reverse("planner:search_locations"), {"name": "D"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"locations": []})
        urlopen.assert_not_called()

    @patch("planner.views.urlopen")
    def test_location_search_maps_provider_results(self, urlopen):
        provider_response = {
            "results": [
                {"name": "Depok", "admin1": "West Java", "country": "Indonesia",
                 "latitude": -6.4, "longitude": 106.8}
            ]
        }
        response_context = urlopen.return_value.__enter__.return_value
        response_context.read.return_value = json.dumps(provider_response).encode("utf-8")

        response = self.client.get(reverse("planner:search_locations"), {"name": "Depok"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["locations"], [{
            "name": "Depok, West Java, Indonesia", "latitude": -6.4, "longitude": 106.8
        }])
        urlopen.assert_called_once()
