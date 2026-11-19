import io

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from closet.models import Item

TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


def photo():
    content = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(content, format="PNG")
    return SimpleUploadedFile("shirt.png", content.getvalue(), content_type="image/png")


@override_settings(STORAGES=TEST_STORAGES)
class ClosetAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.list_url = reverse("closet_api:item_list_create")
        self.item = Item.objects.create(user=self.user, name="Old", category="top", color="white")
        self.other_item = Item.objects.create(user=self.other, name="Private", category="top", color="black")

    def test_authentication_required(self):
        client = APIClient()
        self.assertEqual(client.get(self.list_url).status_code, 401)
        self.assertEqual(client.post(self.list_url, {}).status_code, 401)

    def test_list_is_scoped_to_authenticated_user(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([entry["id"] for entry in response.data], [self.item.id])
        self.assertNotIn(self.other_item.id, [entry["id"] for entry in response.data])

    def test_create_multipart_item_sets_owner_and_optimizes_photo(self):
        response = self.client.post(self.list_url, {
            "photo": photo(), "name": "  New Shirt ", "category": "top", "color": "blue",
            "styles": '["Casual"]', "seasons": '["Spring"]', "weather": '["Hot"]',
        }, format="multipart")
        self.assertEqual(response.status_code, 201, response.data)
        created = Item.objects.get(pk=response.data["id"])
        self.assertEqual(created.user, self.user)
        self.assertEqual(created.name, "New Shirt")
        self.assertTrue(created.photo.name.endswith(".webp"))
        self.assertEqual(response.data["user"], self.user.id)

    def test_create_requires_photo_and_validates_choice_fields(self):
        no_photo = self.client.post(self.list_url, {"name": "No Photo", "category": "top", "color": "blue"}, format="json")
        self.assertEqual(no_photo.status_code, 400)
        bad_style = self.client.post(self.list_url, {
            "photo": photo(), "name": "Bad", "category": "top", "color": "blue", "styles": '["Nope"]',
        }, format="multipart")
        self.assertEqual(bad_style.status_code, 400)
        self.assertIn("styles", bad_style.data)

    def test_retrieve_patch_put_delete_crud(self):
        detail = reverse("closet_api:item_detail", args=[self.item.pk])
        self.assertEqual(self.client.get(detail).status_code, 200)
        patched = self.client.patch(detail, {"name": "Changed", "price": 150000}, format="json")
        self.assertEqual(patched.status_code, 200, patched.data)
        self.item.refresh_from_db()
        self.assertEqual((self.item.name, self.item.price), ("Changed", 150000))
        put = self.client.put(detail, {"photo": photo(), "name": "Replaced", "category": "bottom", "color": "black"}, format="multipart")
        self.assertEqual(put.status_code, 200, put.data)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "Replaced")
        self.assertEqual(self.client.delete(detail).status_code, 204)
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_other_users_item_is_hidden_from_detail_and_mutations(self):
        detail = reverse("closet_api:item_detail", args=[self.other_item.pk])
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertEqual(self.client.patch(detail, {"name": "Stolen"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(detail).status_code, 404)
        self.other_item.refresh_from_db()
        self.assertEqual(self.other_item.name, "Private")
