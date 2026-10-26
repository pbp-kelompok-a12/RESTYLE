from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from closet.models import Item
from community.models import Post
from mixmatch.models import Outfit

User = get_user_model()

def make_item(user, name, category, status="ready"):
    return Item.objects.create(user=user, name=name, category=category, color="red", status=status)

PLAIN_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

@override_settings(STORAGES=PLAIN_STORAGES)
class MixMatchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alsa", password="pw12345!")
        self.other = User.objects.create_user("fadly", password="pw12345!")
        self.top = make_item(self.user, "White Tee", "top")
        self.bottom = make_item(self.user, "Red Skirt", "bottom")
        self.shoes = make_item(self.user, "Heels", "shoes")
        self.jacket = make_item(self.user, "Jacket", "outerwear")
        self.dress = make_item(self.user, "Midi Dress", "dresses")
        self.bag = make_item(self.user, "Tote Bag", "accessories")
        self.washing = make_item(self.user, "Dirty Jeans", "bottom", status="washing")
        self.foreign = make_item(self.other, "Their Top", "top")
        self.client.login(username="alsa", password="pw12345!")

    def payload(self, **extra):
        data = {"name": "Campus day", "notes": "hot day", "tags": ["Casual", "Cozy"],
                "top": self.top.id, "bottom": self.bottom.id, "shoes": self.shoes.id, "accessories": ""}
        data.update(extra)
        return data

    # ---- Read ----
    def test_login_required(self):
        self.client.logout()
        for url in [reverse("mixmatch:show_mixmatch"), reverse("mixmatch:save_outfit")]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response["Location"])

    def test_page_shows_my_closet_only_and_disables_washing(self):
        response = self.client.get(reverse("mixmatch:show_mixmatch"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "White Tee")
        self.assertNotContains(response, "Their Top")
        self.assertContains(response, "In the wash")
        self.assertContains(response, "Rp0")
        self.assertContains(response, "No saved outfits yet")

    # ---- Create ----
    def test_create_outfit(self):
        response = self.client.post(reverse("mixmatch:save_outfit"), self.payload())
        self.assertRedirects(response, reverse("mixmatch:show_mixmatch"))
        outfit = Outfit.objects.get()
        self.assertEqual(outfit.user, self.user)
        self.assertEqual(outfit.tags, ["Casual", "Cozy"])
        self.assertEqual(outfit.pieces, [self.top, self.bottom, self.shoes])
        self.assertContains(self.client.get(reverse("mixmatch:show_mixmatch")), "Campus day")

    def test_cannot_use_someone_elses_item(self):
        response = self.client.post(reverse("mixmatch:save_outfit"), self.payload(top=self.foreign.id))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Outfit.objects.count(), 0)

    def test_item_must_match_slot_category(self):
        response = self.client.post(reverse("mixmatch:save_outfit"), self.payload(top=self.shoes.id))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Outfit.objects.count(), 0)

    def test_outerwear_and_dresses_have_their_own_slots(self):
        response = self.client.post(reverse("mixmatch:save_outfit"),
                                    self.payload(outerwear=self.jacket.id, dresses=self.dress.id))
        self.assertEqual(response.status_code, 302)
        outfit = Outfit.objects.get()
        self.assertEqual(outfit.outerwear, self.jacket)
        self.assertEqual(outfit.dresses, self.dress)
        self.assertEqual(len(outfit.pieces), 5)

    def test_jacket_cannot_go_in_accessories_slot(self):
        response = self.client.post(reverse("mixmatch:save_outfit"), self.payload(accessories=self.jacket.id))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Outfit.objects.count(), 0)

    def test_needs_name_and_at_least_one_piece(self):
        empty = {"name": "Empty", "top": "", "bottom": "", "shoes": "", "accessories": ""}
        self.assertEqual(self.client.post(reverse("mixmatch:save_outfit"), empty).status_code, 400)
        self.assertEqual(self.client.post(reverse("mixmatch:save_outfit"), self.payload(name="   ")).status_code, 400)
        self.assertEqual(Outfit.objects.count(), 0)

    def test_error_keeps_what_user_picked(self):
        response = self.client.post(reverse("mixmatch:save_outfit"), self.payload(name="", top=self.top.id))
        self.assertContains(response, 'value="%d"' % self.top.id, status_code=400)

    # ---- Update ----
    def test_edit_outfit(self):
        outfit = Outfit.objects.create(user=self.user, name="Old", top=self.top)
        page = self.client.get(reverse("mixmatch:edit_outfit", args=[outfit.id]))
        self.assertContains(page, "Update outfit")
        self.assertContains(page, 'value="Old"')
        response = self.client.post(reverse("mixmatch:edit_outfit", args=[outfit.id]),
                                    self.payload(name="New name", shoes=self.shoes.id))
        self.assertRedirects(response, reverse("mixmatch:show_mixmatch"))
        outfit.refresh_from_db()
        self.assertEqual(outfit.name, "New name")
        self.assertEqual(outfit.shoes, self.shoes)

    def test_cannot_edit_someone_elses_outfit(self):
        outfit = Outfit.objects.create(user=self.other, name="Theirs", top=self.foreign)
        self.assertEqual(self.client.get(reverse("mixmatch:edit_outfit", args=[outfit.id])).status_code, 404)
        self.assertEqual(self.client.post(reverse("mixmatch:edit_outfit", args=[outfit.id]), self.payload()).status_code, 404)

    # ---- Delete ----
    def test_delete_outfit(self):
        outfit = Outfit.objects.create(user=self.user, name="Bye", top=self.top)
        url = reverse("mixmatch:delete_outfit", args=[outfit.id])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("mixmatch:show_mixmatch"))
        self.assertFalse(Outfit.objects.exists())

    def test_cannot_delete_someone_elses_outfit(self):
        outfit = Outfit.objects.create(user=self.other, name="Theirs", top=self.foreign)
        self.assertEqual(self.client.post(reverse("mixmatch:delete_outfit", args=[outfit.id])).status_code, 404)
        self.assertTrue(Outfit.objects.filter(id=outfit.id).exists())

    def test_deleting_closet_item_keeps_outfit(self):
        outfit = Outfit.objects.create(user=self.user, name="Keep", top=self.top, bottom=self.bottom)
        self.top.delete()
        outfit.refresh_from_db()
        self.assertIsNone(outfit.top)
        self.assertEqual(outfit.pieces, [self.bottom])
        self.assertEqual(self.client.get(reverse("mixmatch:show_mixmatch")).status_code, 200)

    # ---- Share ----
    def test_share_to_community(self):
        response = self.client.post(reverse("mixmatch:save_outfit"), self.payload(share="1"))
        self.assertRedirects(response, reverse("community:show_community"), fetch_redirect_response=False)
        self.assertEqual(Outfit.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.author, self.user)
        self.assertIn("Campus day", post.content)
        self.assertEqual(set(post.tagged_items.all()), {self.top, self.bottom, self.shoes})

    def test_share_tags_at_most_five_items(self):
        data = self.payload(share="1", accessories=self.bag.id, outerwear=self.jacket.id, dresses=self.dress.id)
        self.client.post(reverse("mixmatch:save_outfit"), data)
        self.assertEqual(len(Outfit.objects.get().pieces), 6)
        self.assertEqual(Post.objects.get().tagged_items.count(), 5)