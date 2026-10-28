import io

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from closet.models import Item
from mixmatch.models import Outfit

# biar test gak upload ke cloudinary
TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


def make_photo():
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, format="PNG")
    return SimpleUploadedFile("photo.png", buffer.getvalue(), content_type="image/png")


@override_settings(STORAGES=TEST_STORAGES)
class ClosetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")

    def test_item_str(self):
        item = Item.objects.create(user=self.user, name="Kaos Putih", category="top", color="white")
        self.assertEqual(str(item), "Kaos Putih (testuser)")

    def test_default_status_is_ready(self):
        item = Item.objects.create(user=self.user, name="Kaos Putih", category="top", color="white")
        self.assertEqual(item.status, "ready")

    def test_color_hex(self):
        item = Item.objects.create(user=self.user, name="Kaos Merah", category="top", color="red")
        self.assertEqual(item.color_hex, Item.COLOR_HEX["red"])


@override_settings(STORAGES=TEST_STORAGES)
class ClosetViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.item = Item.objects.create(user=self.user, name="Kaos Putih", category="top", color="white")

    # ---------- READ ----------
    def test_closet_page_url_exists(self):
        response = self.client.get("/closet/")
        self.assertEqual(response.status_code, 200)

    def test_closet_page_uses_correct_template(self):
        response = self.client.get(reverse("closet:show_closet"))
        self.assertTemplateUsed(response, "closet.html")

    def test_closet_page_shows_item(self):
        response = self.client.get(reverse("closet:show_closet"))
        self.assertContains(response, "Kaos Putih")

    def test_closet_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("closet:show_closet"))
        self.assertEqual(response.status_code, 302)

    def test_filter_by_category(self):
        Item.objects.create(user=self.user, name="Celana Jeans", category="bottom", color="blue")
        response = self.client.get(reverse("closet:show_closet"), {"cat": "bottom"})
        self.assertContains(response, "Celana Jeans")
        self.assertNotContains(response, "Kaos Putih")

    def test_item_detail_page(self):
        response = self.client.get(reverse("closet:show_item_detail", args=[self.item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kaos Putih")

    # ---------- CREATE ----------
    def test_add_item_page_url_exists(self):
        response = self.client.get(reverse("closet:add_item"))
        self.assertEqual(response.status_code, 200)

    def test_add_item(self):
        data = {"name": "Jaket Hitam", "category": "outerwear", "color": "black", "photo": make_photo()}
        response = self.client.post(reverse("closet:add_item"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Item.objects.filter(name="Jaket Hitam").exists())

    def test_add_item_without_photo_fails(self):
        data = {"name": "Jaket Hitam", "category": "outerwear", "color": "black"}
        self.client.post(reverse("closet:add_item"), data)
        self.assertFalse(Item.objects.filter(name="Jaket Hitam").exists())

    # ---------- UPDATE ----------
    def test_edit_item(self):
        data = {"name": "Kaos Hitam", "category": "top", "color": "black", "photo": make_photo()}
        response = self.client.post(reverse("closet:edit_item", args=[self.item.id]), data)
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "Kaos Hitam")

    def test_change_status_updates_planner_outfit(self):
        shoes = Item.objects.create(
            user=self.user, name="Sneakers", category="shoes", color="white"
        )
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
            card["status"] for card in planner_response.json()["outfits"]
            if card["id"] == outfit.id
        )
        self.assertEqual(outfit_status, "washing")

        self.client.post(status_url)
        shoes.refresh_from_db()
        self.assertEqual(shoes.status, "ready")
        planner_response = self.client.get(options_url, {"date": "2026-10-28"})
        outfit_status = next(
            card["status"] for card in planner_response.json()["outfits"]
            if card["id"] == outfit.id
        )
        self.assertEqual(outfit_status, "ready")

    def test_change_status_requires_post_and_owned_manual_status_item(self):
        shoes = Item.objects.create(
            user=self.user, name="Sneakers", category="shoes", color="white"
        )
        status_url = reverse("closet:change_status", args=[shoes.id])
        self.assertEqual(self.client.get(status_url).status_code, 405)

        other = User.objects.create_user(username="other", password="test-password")
        other_shoes = Item.objects.create(
            user=other, name="Other Sneakers", category="shoes", color="black"
        )
        response = self.client.post(
            reverse("closet:change_status", args=[other_shoes.id])
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse("closet:change_status", args=[self.item.id]))
        self.assertEqual(response.status_code, 404)

    # ---------- DELETE ----------
    def test_delete_item(self):
        response = self.client.post(reverse("closet:delete_item", args=[self.item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Item.objects.filter(id=self.item.id).exists())

    # ---------- AKSES ITEM ORANG LAIN ----------
    def test_cannot_open_other_users_item(self):
        other = User.objects.create_user(username="other", password="12345")
        item = Item.objects.create(user=other, name="Punya Orang", category="top", color="red")
        response = self.client.get(reverse("closet:show_item_detail", args=[item.id]))
        self.assertEqual(response.status_code, 404)