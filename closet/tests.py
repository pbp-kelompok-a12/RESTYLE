import io
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from closet.forms import ItemForm
from closet.models import ALL_YEAR, Item
from closet.templatetags.currency_format import rupiah
from mixmatch.models import Outfit

# biar test gak upload ke cloudinary
TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


def make_photo(name="photo.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def make_item(user, name="Kaos Putih", category="top", color="white", **extra):
    return Item.objects.create(user=user, name=name, category=category, color=color, **extra)


def valid_data(**extra):
    data = {"name": "Jaket Hitam", "category": "outerwear", "color": "black"}
    data.update(extra)
    return data

# ---------- MODEL ----------
@override_settings(STORAGES=TEST_STORAGES)
class ClosetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")

    def test_item_str(self):
        item = make_item(self.user)
        self.assertEqual(str(item), "Kaos Putih (testuser)")

    def test_default_status_is_ready(self):
        self.assertEqual(make_item(self.user).status, "ready")

    def test_color_hex(self):
        item = make_item(self.user, color="red")
        self.assertEqual(item.color_hex, Item.COLOR_HEX["red"])

    def test_color_hex_falls_back_for_unknown_color(self):
        item = make_item(self.user, color="unknown")
        self.assertEqual(item.color_hex, "#CCCCCC")

    def test_json_fields_default_to_empty_list(self):
        item = make_item(self.user)
        self.assertEqual(item.styles, [])
        self.assertEqual(item.seasons, [])
        self.assertEqual(item.weather, [])

    def test_change_status_toggles_both_ways(self):
        item = make_item(self.user, category="shoes")
        item.change_status()
        item.refresh_from_db()
        self.assertEqual(item.status, "washing")
        item.change_status()
        item.refresh_from_db()
        self.assertEqual(item.status, "ready")

    def test_items_are_ordered_newest_first(self):
        first = make_item(self.user, name="Lama")
        second = make_item(self.user, name="Baru")
        self.assertEqual(list(Item.objects.all()), [second, first])

    def test_deleting_user_deletes_items(self):
        make_item(self.user)
        self.user.delete()
        self.assertEqual(Item.objects.count(), 0)

# ---------- TEMPLATE TAG ----------
class RupiahFilterTest(TestCase):
    def test_none_becomes_dash(self):
        self.assertEqual(rupiah(None), "-")

    def test_formats_with_dot_separator(self):
        self.assertEqual(rupiah(150000), "Rp 150.000")
        self.assertEqual(rupiah(1500000), "Rp 1.500.000")

    def test_zero(self):
        self.assertEqual(rupiah(0), "Rp 0")


# ---------- FORM ----------
@override_settings(STORAGES=TEST_STORAGES)
class ItemFormTest(TestCase):
    def build(self, data=None, photo=True):
        files = {"photo": make_photo()} if photo else {}
        return ItemForm(data if data is not None else valid_data(), files)

    def test_valid_form(self):
        self.assertTrue(self.build().is_valid())

    def test_photo_is_required(self):
        form = self.build(photo=False)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["photo"], ["Please upload a photo of your item."])

    def test_name_category_color_are_required(self):
        form = self.build({})
        self.assertFalse(form.is_valid())
        for field in ("name", "category", "color"):
            self.assertIn(field, form.errors)

    def test_invalid_category_and_color_are_rejected(self):
        form = self.build(valid_data(category="topi", color="neon"))
        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)
        self.assertIn("color", form.errors)

    def test_name_is_stripped(self):
        form = self.build(valid_data(name="  Jaket Hitam  "))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "Jaket Hitam")

    def test_non_image_file_is_rejected(self):
        fake = SimpleUploadedFile("notes.png", b"not really an image", content_type="image/png")
        form = ItemForm(valid_data(), {"photo": fake})
        self.assertFalse(form.is_valid())
        self.assertIn("photo", form.errors)

    def test_photo_over_10mb_is_rejected(self):
        photo = make_photo()
        photo.size = 11 * 1024 * 1024
        form = ItemForm(valid_data(), {"photo": photo})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["photo"], ["The photo must be 10 MB or smaller."])

    def test_photo_is_converted_to_webp(self):
        form = self.build()
        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data["photo"].name.endswith(".webp"))

    def test_future_purchase_date_is_rejected(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        form = self.build(valid_data(date_purchased=tomorrow.isoformat()))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["date_purchased"], ["Purchase date can't be in the future."])

    def test_today_and_past_purchase_date_are_accepted(self):
        today = timezone.localdate()
        for day in (today, today - timedelta(days=30)):
            with self.subTest(day=day):
                self.assertTrue(self.build(valid_data(date_purchased=day.isoformat())).is_valid())

    def test_price_with_dots_is_parsed_to_int(self):
        form = self.build(valid_data(price="1.500.000"))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["price"], 1500000)

    def test_empty_price_becomes_none(self):
        form = self.build(valid_data(price=""))
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["price"])

    def test_price_with_letters_is_rejected(self):
        form = self.build(valid_data(price="abc"))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["price"], ["Enter a valid price."])

    def test_negative_price_is_rejected(self):
        form = self.build(valid_data(price="-5000"))
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_all_year_round_replaces_other_seasons(self):
        form = self.build(valid_data(seasons=["Spring", ALL_YEAR]))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["seasons"], [ALL_YEAR])

    def test_normal_seasons_are_kept(self):
        form = self.build(valid_data(seasons=["Spring", "Winter"]))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["seasons"], ["Spring", "Winter"])

    def test_invalid_style_tag_is_rejected(self):
        form = self.build(valid_data(styles=["Casual", "Gaje"]))
        self.assertFalse(form.is_valid())
        self.assertIn("styles", form.errors)

    def test_invalid_purchase_link_is_rejected(self):
        form = self.build(valid_data(purchase_link="bukan url"))
        self.assertFalse(form.is_valid())
        self.assertIn("purchase_link", form.errors)

    def test_valid_purchase_link_is_accepted(self):
        form = self.build(valid_data(purchase_link="https://www.uniqlo.com/id/shirt"))
        self.assertTrue(form.is_valid())

# ---------- VIEW: READ (list, detail, filter) ----------
@override_settings(STORAGES=TEST_STORAGES)
class ClosetReadTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.item = make_item(self.user)

    def test_closet_page_url_exists(self):
        self.assertEqual(self.client.get("/closet/").status_code, 200)

    def test_closet_page_uses_correct_template(self):
        response = self.client.get(reverse("closet:show_closet"))
        self.assertTemplateUsed(response, "closet.html")

    def test_closet_page_shows_item(self):
        response = self.client.get(reverse("closet:show_closet"))
        self.assertContains(response, "Kaos Putih")

    def test_closet_only_shows_my_items(self):
        other = User.objects.create_user(username="other", password="12345")
        make_item(other, name="Punya Orang")
        response = self.client.get(reverse("closet:show_closet"))
        self.assertNotContains(response, "Punya Orang")
        self.assertEqual(response.context["total_count"], 1)

    def test_empty_closet_shows_empty_state(self):
        Item.objects.all().delete()
        response = self.client.get(reverse("closet:show_closet"))
        self.assertContains(response, "Your closet is empty")

    def test_item_detail_page(self):
        response = self.client.get(reverse("closet:show_item_detail", args=[self.item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "item_detail.html")
        self.assertContains(response, "Kaos Putih")

    def test_item_detail_shows_formatted_price(self):
        self.item.price = 150000
        self.item.save()
        response = self.client.get(reverse("closet:show_item_detail", args=[self.item.id]))
        self.assertContains(response, "Rp 150.000")

    def test_item_detail_modal_uses_partial_template(self):
        response = self.client.get(reverse("closet:show_item_detail", args=[self.item.id]), {"modal": "1"})
        self.assertTemplateUsed(response, "_item_detail.html")
        self.assertTemplateNotUsed(response, "item_detail.html")

    def test_item_detail_with_fetch_header_uses_partial_template(self):
        response = self.client.get(
            reverse("closet:show_item_detail", args=[self.item.id]),
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertTemplateUsed(response, "_item_detail.html")

    def test_item_detail_for_missing_item_is_404(self):
        response = self.client.get(reverse("closet:show_item_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_shoes_and_accessories_show_status_button_but_tops_do_not(self):
        response = self.client.get(reverse("closet:show_closet"))
        self.assertNotContains(response, "Change to In The Wash")
        make_item(self.user, name="Sneakers", category="shoes", color="black")
        response = self.client.get(reverse("closet:show_closet"))
        self.assertContains(response, "Change to In The Wash")

    def test_visiting_closet_syncs_automatic_status_back_to_ready(self):
        self.item.status = "washing"
        self.item.save()
        self.client.get(reverse("closet:show_closet"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "ready")


@override_settings(STORAGES=TEST_STORAGES)
class ClosetFilterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.url = reverse("closet:show_closet")
        self.shirt = make_item(
            self.user, name="Kaos Putih", category="top", color="white",
            styles=["Casual"], seasons=["Summer"], weather=["Hot"],
            store="Uniqlo", material="cotton",
        )
        self.jeans = make_item(
            self.user, name="Celana Jeans", category="bottom", color="blue",
            styles=["Street"], seasons=[ALL_YEAR], weather=["Rainy"], material="denim",
        )
        self.shoes = make_item(
            self.user, name="Sneakers", category="shoes", color="black",
            styles=["Sporty"], store="Nike", status="washing",
        )

    def names(self, **params):
        response = self.client.get(self.url, params)
        return {item.name for item in response.context["items"]}

    def test_no_filter_shows_everything(self):
        self.assertEqual(self.names(), {"Kaos Putih", "Celana Jeans", "Sneakers"})

    def test_filter_by_category(self):
        self.assertEqual(self.names(cat="bottom"), {"Celana Jeans"})

    def test_filter_by_color(self):
        self.assertEqual(self.names(color="blue"), {"Celana Jeans"})

    def test_filter_by_status(self):
        self.assertEqual(self.names(status="washing"), {"Sneakers"})

    def test_filter_by_style(self):
        self.assertEqual(self.names(style="Casual"), {"Kaos Putih"})

    def test_filter_by_season(self):
        self.assertEqual(self.names(season="Summer"), {"Kaos Putih", "Celana Jeans"})

    def test_all_year_items_match_every_season(self):
        self.assertEqual(self.names(season="Winter"), {"Celana Jeans"})

    def test_filter_by_weather(self):
        self.assertEqual(self.names(weather="Rainy"), {"Celana Jeans"})

    def test_search_by_name_store_and_material(self):
        self.assertEqual(self.names(q="jeans"), {"Celana Jeans"})
        self.assertEqual(self.names(q="UNIQLO"), {"Kaos Putih"})
        self.assertEqual(self.names(q="denim"), {"Celana Jeans"})
        self.assertEqual(self.names(q="nike"), {"Sneakers"})

    def test_filters_can_be_combined(self):
        self.assertEqual(self.names(cat="top", color="white"), {"Kaos Putih"})
        self.assertEqual(self.names(cat="top", color="blue"), set())

    def test_blank_filter_values_are_ignored(self):
        self.assertEqual(self.names(cat="", color="  "), {"Kaos Putih", "Celana Jeans", "Sneakers"})

    def test_no_match_shows_message_and_clear_link(self):
        response = self.client.get(self.url, {"cat": "top", "color": "blue"})
        self.assertContains(response, "No items match")
        self.assertTrue(response.context["has_filters"])

    def test_counts_in_context(self):
        response = self.client.get(self.url, {"cat": "top"})
        self.assertEqual(response.context["shown_count"], 1)
        self.assertEqual(response.context["total_count"], 3)

    def test_category_chip_marks_selected_category(self):
        response = self.client.get(self.url, {"cat": "bottom"})
        chips = {chip["label"]: chip["active"] for chip in response.context["cat_chips"]}
        self.assertTrue(chips["Bottom"])
        self.assertFalse(chips["All"])

    def test_chip_url_keeps_other_filters(self):
        response = self.client.get(self.url, {"cat": "top", "color": "white"})
        chips = {chip["label"]: chip["url"] for chip in response.context["cat_chips"]}
        self.assertIn("color=white", chips["Bottom"])
        self.assertNotIn("cat=top", chips["Bottom"])
        self.assertNotIn("cat=", chips["All"])

# ---------- VIEW: CREATE ----------
@override_settings(STORAGES=TEST_STORAGES)
class ClosetCreateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.url = reverse("closet:add_item")

    def test_add_item_page_url_exists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "item_form.html")

    def test_add_item_modal_get_uses_partial_template(self):
        response = self.client.get(self.url, {"modal": "1"})
        self.assertTemplateUsed(response, "_item_form.html")
        self.assertTemplateNotUsed(response, "item_form.html")

    def test_add_item(self):
        response = self.client.post(self.url, valid_data(photo=make_photo()))
        self.assertRedirects(response, reverse("closet:show_closet"))
        item = Item.objects.get(name="Jaket Hitam")
        self.assertEqual(item.user, self.user)
        self.assertTrue(item.photo.name.endswith(".webp"))

    def test_add_item_saves_all_optional_fields(self):
        data = valid_data(
            photo=make_photo(), material="cotton", styles=["Casual", "Cozy"],
            seasons=["Winter"], weather=["Cool"], store="Uniqlo",
            purchase_link="https://uniqlo.com", date_purchased="2026-01-15", price="250.000",
        )
        self.client.post(self.url, data)
        item = Item.objects.get(name="Jaket Hitam")
        self.assertEqual(item.styles, ["Casual", "Cozy"])
        self.assertEqual(item.seasons, ["Winter"])
        self.assertEqual(item.weather, ["Cool"])
        self.assertEqual(item.store, "Uniqlo")
        self.assertEqual(item.price, 250000)
        self.assertEqual(item.date_purchased.isoformat(), "2026-01-15")

    def test_add_item_shows_success_message(self):
        self.client.post(self.url, valid_data(photo=make_photo()))
        messages = [str(m) for m in get_messages(self.client.get(self.url).wsgi_request)]
        self.assertTrue(any("Jaket Hitam" in m for m in messages))

    def test_user_cannot_be_forged_through_post_data(self):
        other = User.objects.create_user(username="other", password="12345")
        self.client.post(self.url, valid_data(photo=make_photo(), user=other.id))
        self.assertEqual(Item.objects.get(name="Jaket Hitam").user, self.user)

    def test_add_item_without_photo_fails(self):
        response = self.client.post(self.url, valid_data())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Item.objects.filter(name="Jaket Hitam").exists())

    def test_add_item_with_invalid_data_shows_errors(self):
        response = self.client.post(self.url, valid_data(photo=make_photo(), price="abc"))
        self.assertContains(response, "Enter a valid price.")
        self.assertEqual(Item.objects.count(), 0)

    def test_add_item_modal_success_returns_json(self):
        response = self.client.post(self.url + "?modal=1", valid_data(photo=make_photo()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertTrue(Item.objects.filter(name="Jaket Hitam").exists())

    def test_add_item_fetch_header_success_returns_json(self):
        response = self.client.post(
            self.url, valid_data(photo=make_photo()), HTTP_X_REQUESTED_WITH="fetch"
        )
        self.assertEqual(response.json(), {"ok": True})

    def test_add_item_modal_invalid_returns_400_with_form(self):
        response = self.client.post(self.url + "?modal=1", valid_data())
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, "_item_form.html")
        self.assertFalse(Item.objects.exists())

# ---------- VIEW: UPDATE ----------
@override_settings(STORAGES=TEST_STORAGES)
class ClosetUpdateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.item = make_item(self.user, photo=make_photo("old.png"))
        self.url = reverse("closet:edit_item", args=[self.item.id])

    def test_edit_page_is_prefilled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "item_form.html")
        self.assertContains(response, "Kaos Putih")

    def test_edit_item(self):
        data = {"name": "Kaos Hitam", "category": "top", "color": "black", "photo": make_photo()}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse("closet:show_item_detail", args=[self.item.id]))
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "Kaos Hitam")
        self.assertEqual(self.item.color, "black")

    def test_edit_without_new_photo_keeps_old_photo(self):
        old_photo = self.item.photo.name
        response = self.client.post(self.url, {"name": "Kaos Baru", "category": "top", "color": "white"})
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "Kaos Baru")
        self.assertEqual(self.item.photo.name, old_photo)

    def test_edit_can_clear_optional_fields(self):
        self.item.price = 100000
        self.item.styles = ["Casual"]
        self.item.save()
        self.client.post(self.url, {"name": "Kaos Putih", "category": "top", "color": "white", "price": ""})
        self.item.refresh_from_db()
        self.assertIsNone(self.item.price)
        self.assertEqual(self.item.styles, [])

    def test_edit_with_invalid_data_does_not_change_item(self):
        response = self.client.post(self.url, {"name": "", "category": "top", "color": "white"})
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "Kaos Putih")

    def test_edit_modal_success_returns_json(self):
        data = {"name": "Kaos Modal", "category": "top", "color": "white"}
        response = self.client.post(self.url + "?modal=1", data)
        self.assertEqual(response.json(), {"ok": True})
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "Kaos Modal")

    def test_edit_modal_invalid_returns_400(self):
        response = self.client.post(self.url + "?modal=1", {"name": "", "category": "top", "color": "white"})
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, "_item_form.html")

    def test_edit_modal_get_uses_partial_template(self):
        response = self.client.get(self.url, {"modal": "1"})
        self.assertTemplateUsed(response, "_item_form.html")


@override_settings(STORAGES=TEST_STORAGES)
class ClosetChangeStatusTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_change_status_updates_planner_outfit(self):
        shoes = make_item(self.user, name="Sneakers", category="shoes")
        outfit = Outfit.objects.create(user=self.user, name="Sneaker Outfit", shoes=shoes)
        status_url = reverse("closet:change_status", args=[shoes.id])
        options_url = reverse("planner:outfit_options")

        response = self.client.post(status_url)
        self.assertRedirects(response, reverse("closet:show_closet"))
        shoes.refresh_from_db()
        self.assertEqual(shoes.status, "washing")

        planner_response = self.client.get(options_url, {"date": "2026-10-28"})
        self.assertEqual(planner_response.status_code, 200)
        outfit_status = next(
            card["status"] for card in planner_response.json()["outfits"] if card["id"] == outfit.id
        )
        self.assertEqual(outfit_status, "washing")

        self.client.post(status_url)
        shoes.refresh_from_db()
        self.assertEqual(shoes.status, "ready")
        planner_response = self.client.get(options_url, {"date": "2026-10-28"})
        outfit_status = next(
            card["status"] for card in planner_response.json()["outfits"] if card["id"] == outfit.id
        )
        self.assertEqual(outfit_status, "ready")

    def test_change_status_works_for_accessories(self):
        bag = make_item(self.user, name="Tote Bag", category="accessories")
        self.client.post(reverse("closet:change_status", args=[bag.id]))
        bag.refresh_from_db()
        self.assertEqual(bag.status, "washing")

    def test_change_status_shows_message(self):
        shoes = make_item(self.user, name="Sneakers", category="shoes")
        response = self.client.post(reverse("closet:change_status", args=[shoes.id]), follow=True)
        self.assertContains(response, "Sneakers")
        self.assertContains(response, "in the wash")

    def test_change_status_requires_post(self):
        shoes = make_item(self.user, name="Sneakers", category="shoes")
        response = self.client.get(reverse("closet:change_status", args=[shoes.id]))
        self.assertEqual(response.status_code, 405)

    def test_change_status_rejects_other_users_item(self):
        other = User.objects.create_user(username="other", password="test-password")
        other_shoes = make_item(other, name="Other Sneakers", category="shoes", color="black")
        response = self.client.post(reverse("closet:change_status", args=[other_shoes.id]))
        self.assertEqual(response.status_code, 404)
        other_shoes.refresh_from_db()
        self.assertEqual(other_shoes.status, "ready")

    def test_change_status_rejects_automatic_categories(self):
        top = make_item(self.user)
        response = self.client.post(reverse("closet:change_status", args=[top.id]))
        self.assertEqual(response.status_code, 404)

# ---------- VIEW: DELETE ----------
@override_settings(STORAGES=TEST_STORAGES)
class ClosetDeleteTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.item = make_item(self.user)
        self.url = reverse("closet:delete_item", args=[self.item.id])

    def test_delete_item(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("closet:show_closet"))
        self.assertFalse(Item.objects.filter(id=self.item.id).exists())

    def test_delete_requires_post(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertTrue(Item.objects.filter(id=self.item.id).exists())

    def test_delete_modal_returns_json(self):
        response = self.client.post(self.url + "?modal=1")
        self.assertEqual(response.json(), {"ok": True})
        self.assertFalse(Item.objects.filter(id=self.item.id).exists())

    def test_delete_shows_message_with_item_name(self):
        response = self.client.post(self.url, follow=True)
        self.assertContains(response, "was removed from your closet")

    def test_deleting_item_keeps_outfit_but_empties_slot(self):
        outfit = Outfit.objects.create(user=self.user, name="Outfit", top=self.item)
        self.client.post(self.url)
        outfit.refresh_from_db()
        self.assertIsNone(outfit.top)

# ---------- SECURITY: login + akses item orang lain ----------
@override_settings(STORAGES=TEST_STORAGES)
class ClosetSecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.other = User.objects.create_user(username="other", password="12345")
        self.their_item = make_item(self.other, name="Punya Orang", color="red")
        self.client.login(username="testuser", password="12345")

    def test_all_endpoints_require_login(self):
        self.client.logout()
        item_id = self.their_item.id
        endpoints = [
            ("get", reverse("closet:show_closet")),
            ("get", reverse("closet:add_item")),
            ("get", reverse("closet:show_item_detail", args=[item_id])),
            ("get", reverse("closet:edit_item", args=[item_id])),
            ("post", reverse("closet:change_status", args=[item_id])),
            ("post", reverse("closet:delete_item", args=[item_id])),
        ]
        for method, url in endpoints:
            with self.subTest(url=url):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith("/login"))

    def test_cannot_open_other_users_item(self):
        response = self.client.get(reverse("closet:show_item_detail", args=[self.their_item.id]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_open_edit_page_of_other_users_item(self):
        response = self.client.get(reverse("closet:edit_item", args=[self.their_item.id]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_edit_other_users_item(self):
        data = {"name": "Dibajak", "category": "top", "color": "red", "photo": make_photo()}
        response = self.client.post(reverse("closet:edit_item", args=[self.their_item.id]), data)
        self.assertEqual(response.status_code, 404)
        self.their_item.refresh_from_db()
        self.assertEqual(self.their_item.name, "Punya Orang")

    def test_cannot_delete_other_users_item(self):
        response = self.client.post(reverse("closet:delete_item", args=[self.their_item.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Item.objects.filter(id=self.their_item.id).exists())

    def test_modal_requests_also_respect_ownership(self):
        response = self.client.get(
            reverse("closet:show_item_detail", args=[self.their_item.id]), {"modal": "1"}
        )
        self.assertEqual(response.status_code, 404)