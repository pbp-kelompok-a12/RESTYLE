import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from community.models import Comment, CommunityProfile, Follow, Notification, Post, PostImage
from closet.models import Item

SIMPLE_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

@override_settings(STORAGES=SIMPLE_STORAGES)
class FollowProfileViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.alice = user_model.objects.create_user(
            username="alice",
            password="test-password",
        )
        self.bob = user_model.objects.create_user(
            username="bob",
            password="test-password",
        )
        self.client.force_login(self.alice)

    def test_profile_shows_follow_counts_and_follow_state(self):
        Follow.objects.create(follower=self.alice, followed=self.bob)

        response = self.client.get("/community/profile/bob/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-followers-count>1</strong>')
        self.assertContains(response, ">Following</span>")
        self.assertContains(response, 'href="/community/profile/bob/followers/"')
        self.assertContains(response, 'href="/community/profile/bob/following/"')

    def test_following_list_shows_people_followed_by_profile_user(self):
        Follow.objects.create(follower=self.alice, followed=self.bob)

        response = self.client.get("/community/profile/alice/following/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@bob")
        self.assertContains(response, ">Following</span>")

    def test_followers_list_shows_people_who_follow_profile_user(self):
        Follow.objects.create(follower=self.alice, followed=self.bob)

        response = self.client.get("/community/profile/bob/followers/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@alice")

    def test_follow_lists_show_empty_state(self):
        response = self.client.get("/community/profile/alice/followers/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No followers yet")


@override_settings(STORAGES=SIMPLE_STORAGES)
class AnonymousCommunityTests(TestCase):
    def setUp(self):
        author = get_user_model().objects.create_user(
            username="author",
            password="test-password",
        )
        self.post = Post.objects.create(author=author, content="A community post")
        Comment.objects.create(post=self.post, author=author, content="A community reply")

    def test_anonymous_user_can_view_feed_and_is_prompted_to_log_in_for_actions(self):
        response = self.client.get("/community/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A community post")
        self.assertContains(response, 'class="cm-react" href="/login/" aria-label="Like this post"')
        self.assertContains(response, 'class="cm-toggle-comments" href="/login/"')
        self.assertContains(response, 'class="cm-react" href="/login/" aria-label="Like this reply"')
        self.assertContains(response, 'class="cm-toggle-reply" href="/login/"')
        self.assertContains(response, "data-login-url=\"/login/\"")
        self.assertContains(response, "Sign in to reply.")

    def test_anonymous_user_is_redirected_to_login_for_following_feed(self):
        response = self.client.get("/community/?tab=following")

        self.assertRedirects(response, "/login/", fetch_redirect_response=False)

    def test_anonymous_user_is_redirected_to_login_for_like_action(self):
        response = self.client.post(f"/community/post/{self.post.id}/like/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/login/?next=/community/post/{self.post.id}/like/")

    def test_anonymous_user_can_browse_profiles_and_follow_lists(self):
        profile_response = self.client.get("/community/profile/author/")
        following_response = self.client.get("/community/profile/author/following/")

        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, "data-login-url=\"/login/\"")
        self.assertEqual(following_response.status_code, 200)

def make_photo(name="photo.png"):
    """bikin file foto PNG kecil untuk keperluan test."""
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(STORAGES=SIMPLE_STORAGES)
class EditPostPhotoTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(
            username="author",
            password="test-password",
        )
        self.client.force_login(self.author)
        self.post = Post.objects.create(author=self.author, content="My outfit")
        self.old_photo = PostImage.objects.create(post=self.post, image=make_photo("old.png"))
        self.edit_url = f"/community/post/{self.post.id}/edit/"

    def test_author_can_remove_old_photo_and_add_new_one(self):
        response = self.client.post(self.edit_url, {
            "content": "My outfit, updated",
            "remove_photos": [self.old_photo.id],
            "photos": [make_photo("new.png")],
        })

        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, "My outfit, updated")
        self.assertFalse(PostImage.objects.filter(id=self.old_photo.id).exists())
        self.assertEqual(self.post.images.count(), 1)

    def test_edit_is_rejected_when_photos_go_over_the_limit(self):
        response = self.client.post(self.edit_url, {
            "content": "Too many photos",
            "photos": [make_photo(f"new{number}.png") for number in range(3)],
        })

        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, "My outfit")
        self.assertEqual(self.post.images.count(), 1)

    def test_other_user_cannot_edit_photos(self):
        other = get_user_model().objects.create_user(username="other", password="test-password")
        self.client.force_login(other)

        response = self.client.post(self.edit_url, {
            "content": "Not mine",
            "remove_photos": [self.old_photo.id],
        })

        self.assertEqual(response.status_code, 403)
        self.assertTrue(PostImage.objects.filter(id=self.old_photo.id).exists())

    def test_feed_shows_photo_edit_controls_to_author(self):
        response = self.client.get("/community/")

        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, f'name="remove_photos" value="{self.old_photo.id}"')

@override_settings(STORAGES=SIMPLE_STORAGES)
class TagClosetItemsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.alice = user_model.objects.create_user(username="alice", password="test-password")
        self.bob = user_model.objects.create_user(username="bob", password="test-password")
        self.client.force_login(self.alice)
        self.shirt = Item.objects.create(user=self.alice, name="Blue linen shirt", category="top", color="blue")
        self.skirt = Item.objects.create(user=self.alice, name="Pleated skirt", category="bottom", color="beige")
        self.bob_shoes = Item.objects.create(user=self.bob, name="Bob's sneakers", category="shoes", color="white")

    def test_post_can_tag_own_closet_items(self):
        self.client.post("/community/post/create/", {
            "content": "Today's outfit",
            "tagged_items": [self.shirt.id, self.skirt.id],
        })

        post = Post.objects.get(content="Today's outfit")
        self.assertEqual(set(post.tagged_items.all()), {self.shirt, self.skirt})

    def test_items_from_someone_elses_closet_are_ignored(self):
        self.client.post("/community/post/create/", {
            "content": "Sneaky tag",
            "tagged_items": [self.shirt.id, self.bob_shoes.id],
        })

        post = Post.objects.get(content="Sneaky tag")
        self.assertEqual(list(post.tagged_items.all()), [self.shirt])

    def test_post_is_rejected_when_tagging_more_than_five_items(self):
        items = [
            Item.objects.create(user=self.alice, name=f"Item {number}", category="top", color="red")
            for number in range(6)
        ]

        self.client.post("/community/post/create/", {
            "content": "Too many tags",
            "tagged_items": [item.id for item in items],
        })

        self.assertFalse(Post.objects.filter(content="Too many tags").exists())

    def test_edit_post_can_change_tags(self):
        post = Post.objects.create(author=self.alice, content="Outfit")
        post.tagged_items.add(self.shirt)

        self.client.post(f"/community/post/{post.id}/edit/", {
            "content": "Outfit",
            "tagged_items": [self.skirt.id],
        })

        self.assertEqual(list(post.tagged_items.all()), [self.skirt])

    def test_feed_shows_tags_and_picker(self):
        post = Post.objects.create(author=self.alice, content="Outfit")
        post.tagged_items.add(self.shirt)

        response = self.client.get("/community/")

        self.assertContains(response, 'class="cm-tags"')
        self.assertContains(response, f'data-closet-url="/closet/item/{self.shirt.id}/"')
        self.assertContains(response, f'name="tagged_items" value="{self.skirt.id}"')
        self.assertNotContains(response, f'name="tagged_items" value="{self.bob_shoes.id}"')

    def test_other_people_can_see_item_details_but_not_closet_link(self):
        post = Post.objects.create(author=self.alice, content="Outfit")
        post.tagged_items.add(self.shirt)
        self.client.force_login(self.bob)

        response = self.client.get("/community/")

        self.assertContains(response, 'data-name="Blue linen shirt"')
        self.assertContains(response, 'data-category="Top"')
        self.assertContains(response, 'data-color="Blue"')
        self.assertNotContains(response, "data-closet-url")

    def test_logged_out_visitors_can_see_item_details(self):
        post = Post.objects.create(author=self.alice, content="Outfit")
        post.tagged_items.add(self.shirt)
        self.client.logout()

        response = self.client.get("/community/")

        self.assertContains(response, 'data-name="Blue linen shirt"')
        self.assertNotContains(response, "data-closet-url")

@override_settings(STORAGES=SIMPLE_STORAGES)
class NotificationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.alice = user_model.objects.create_user(username="alice", password="test-password")
        self.bob = user_model.objects.create_user(username="bob", password="test-password")
        self.carol = user_model.objects.create_user(username="carol", password="test-password")
        self.post = Post.objects.create(author=self.alice, content="Is this outfit okay?")

    def test_reply_notifies_post_author(self):
        self.client.force_login(self.bob)

        self.client.post(f"/community/post/{self.post.id}/comment/", {"content": "Not at all! Just add a cardigan"})

        note = Notification.objects.get(recipient=self.alice)
        self.assertEqual(note.kind, Notification.REPLY)
        self.assertEqual(note.actor, self.bob)
        self.assertEqual(note.message, "replied to your post: “Not at all! Just add a cardigan”")

    def test_reply_to_a_comment_also_notifies_that_comment_author(self):
        comment = Comment.objects.create(post=self.post, author=self.bob, content="Cute!")
        self.client.force_login(self.carol)

        self.client.post(f"/community/post/{self.post.id}/comment/", {"content": "Agree", "parent": comment.id})

        self.assertTrue(Notification.objects.filter(recipient=self.alice, kind=Notification.REPLY).exists())
        bob_note = Notification.objects.get(recipient=self.bob)
        self.assertEqual(bob_note.message, "replied to your comment: “Agree”")

    def test_no_notification_for_your_own_actions(self):
        self.client.force_login(self.alice)

        self.client.post(f"/community/post/{self.post.id}/comment/", {"content": "Thanks all"})
        self.client.post(f"/community/post/{self.post.id}/like/")

        self.assertFalse(Notification.objects.exists())

    def test_likes_are_grouped_into_one_notification(self):
        for user in [self.bob, self.carol]:
            self.client.force_login(user)
            self.client.post(f"/community/post/{self.post.id}/like/")

        note = Notification.objects.get(recipient=self.alice)
        self.assertEqual(note.actor, self.carol)
        self.assertEqual(note.message, "and 1 other liked your post")

    def test_unlike_updates_or_removes_the_like_notification(self):
        for user in [self.bob, self.carol]:
            self.client.force_login(user)
            self.client.post(f"/community/post/{self.post.id}/like/")

        self.client.post(f"/community/post/{self.post.id}/like/")  # carol batal like
        note = Notification.objects.get(recipient=self.alice)
        self.assertEqual(note.actor, self.bob)
        self.assertEqual(note.message, "liked your post")

        self.client.force_login(self.bob)
        self.client.post(f"/community/post/{self.post.id}/like/")  # bob batal like
        self.assertFalse(Notification.objects.exists())

    def test_follow_and_unfollow(self):
        self.client.force_login(self.bob)

        self.client.post("/community/user/alice/follow/")
        note = Notification.objects.get(recipient=self.alice)
        self.assertEqual(note.message, "started following you")

        self.client.post("/community/user/alice/follow/")
        self.assertFalse(Notification.objects.exists())

    def test_navbar_shows_unread_notifications(self):
        Notification.objects.create(recipient=self.alice, actor=self.bob, kind=Notification.FOLLOW)
        self.client.force_login(self.alice)

        response = self.client.get("/community/")

        self.assertContains(response, 'class="nt-badge"')
        self.assertContains(response, "@bob</strong> started following you")
        self.assertContains(response, "Mark all as read")

    def test_navbar_shows_empty_state(self):
        self.client.force_login(self.alice)

        response = self.client.get("/community/")

        self.assertContains(response, "You're all caught up")
        self.assertNotContains(response, 'class="nt-badge"')

    def test_opening_a_notification_marks_it_read_and_goes_to_target(self):
        note = Notification.objects.create(recipient=self.alice, actor=self.bob, kind=Notification.FOLLOW)
        self.client.force_login(self.alice)

        response = self.client.get(f"/community/notifications/{note.id}/")

        self.assertRedirects(response, "/community/profile/bob/", fetch_redirect_response=False)
        note.refresh_from_db()
        self.assertTrue(note.is_read)

    def test_cannot_open_someone_elses_notification(self):
        note = Notification.objects.create(recipient=self.alice, actor=self.bob, kind=Notification.FOLLOW)
        self.client.force_login(self.carol)

        response = self.client.get(f"/community/notifications/{note.id}/")

        self.assertEqual(response.status_code, 404)

    def test_mark_all_as_read(self):
        Notification.objects.create(recipient=self.alice, actor=self.bob, kind=Notification.FOLLOW)
        Notification.objects.create(recipient=self.alice, actor=self.carol, kind=Notification.FOLLOW)
        self.client.force_login(self.alice)

        response = self.client.post("/community/notifications/read/", HTTP_X_REQUESTED_WITH="fetch")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Notification.objects.filter(is_read=False).exists())

    def test_see_all_page(self):
        Notification.objects.create(recipient=self.alice, actor=self.bob, kind=Notification.FOLLOW)
        self.client.force_login(self.alice)

        response = self.client.get("/community/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@bob</strong> started following you")

@override_settings(STORAGES=SIMPLE_STORAGES)
class ProfilePhotoAndSidebarTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.alice = user_model.objects.create_user(username="alice", password="test-password")
        self.bob = user_model.objects.create_user(username="bob", password="test-password")
        self.client.force_login(self.alice)

    def test_user_can_upload_profile_photo(self):
        response = self.client.post("/community/profile/photo/", {"photo": make_photo("me.png")})

        self.assertRedirects(response, "/community/profile/alice/", fetch_redirect_response=False)
        self.assertTrue(CommunityProfile.objects.get(user=self.alice).photo)

    def test_non_image_file_is_rejected(self):
        fake = SimpleUploadedFile("notes.png", b"not really an image", content_type="image/png")

        self.client.post("/community/profile/photo/", {"photo": fake})

        self.assertFalse(CommunityProfile.objects.filter(user=self.alice).exclude(photo="").exists())

    def test_user_can_remove_profile_photo(self):
        self.client.post("/community/profile/photo/", {"photo": make_photo("me.png")})

        self.client.post("/community/profile/photo/", {"remove": "1"})

        self.assertFalse(CommunityProfile.objects.get(user=self.alice).photo)

    def test_photo_is_shown_in_posts_and_navbar(self):
        self.client.post("/community/profile/photo/", {"photo": make_photo("me.png")})
        Post.objects.create(author=self.alice, content="Hello")
        self.client.force_login(self.bob)

        response = self.client.get("/community/")

        self.assertContains(response, 'class="avatar-photo"')

    def test_own_profile_has_sidebar_and_photo_form(self):
        response = self.client.get("/community/profile/alice/")

        self.assertContains(response, 'class="cm-side"')
        self.assertContains(response, 'class="cm-side-link is-active"')
        self.assertContains(response, 'action="/community/profile/photo/"')

    def test_other_profile_has_sidebar_but_no_photo_form(self):
        response = self.client.get("/community/profile/bob/")

        self.assertContains(response, 'class="cm-side"')
        self.assertNotContains(response, 'action="/community/profile/photo/"')


@override_settings(STORAGES=SIMPLE_STORAGES)
class ModerationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(username="admin", password="test-password", is_staff=True)
        self.alice = user_model.objects.create_user(username="alice", password="test-password")
        self.bob = user_model.objects.create_user(username="bob", password="test-password")
        self.post = Post.objects.create(author=self.alice, content="Buy cheap followers here!!!")
        self.other_post = Post.objects.create(author=self.bob, content="My linen outfit")
        self.comment = Comment.objects.create(post=self.other_post, author=self.alice, content="Rude reply")

    def test_regular_user_cannot_open_moderation(self):
        self.client.force_login(self.alice)

        response = self.client.get("/community/moderation/")

        self.assertEqual(response.status_code, 403)

    def test_logged_out_visitor_is_sent_to_login(self):
        response = self.client.get("/community/moderation/")

        self.assertEqual(response.status_code, 302)

    def test_admin_sees_posts_and_stats(self):
        self.client.force_login(self.admin)

        response = self.client.get("/community/moderation/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buy cheap followers here!!!")
        self.assertContains(response, "My linen outfit")
        self.assertContains(response, "<dd>2</dd>", html=True)

    def test_admin_can_search(self):
        self.client.force_login(self.admin)

        response = self.client.get("/community/moderation/?q=followers")

        self.assertContains(response, "Buy cheap followers here!!!")
        self.assertNotContains(response, "My linen outfit")

    def test_admin_sees_replies_tab(self):
        self.client.force_login(self.admin)

        response = self.client.get("/community/moderation/?tab=comments")

        self.assertContains(response, "Rude reply")
        self.assertContains(response, f'action="/community/comment/{self.comment.id}/delete/"')

    def test_admin_can_delete_post_and_return_to_moderation(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            f"/community/post/{self.post.id}/delete/",
            {"next": "/community/moderation/?q=followers"},
        )

        self.assertRedirects(response, "/community/moderation/?q=followers", fetch_redirect_response=False)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_admin_can_delete_comment(self):
        self.client.force_login(self.admin)

        self.client.post(f"/community/comment/{self.comment.id}/delete/", {"next": "/community/moderation/?tab=comments"})

        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_next_to_another_website_is_ignored(self):
        self.client.force_login(self.admin)

        response = self.client.post(f"/community/post/{self.post.id}/delete/", {"next": "https://evil.example.com/"})

        self.assertRedirects(response, "/community/", fetch_redirect_response=False)

    def test_regular_user_still_cannot_delete_others_posts(self):
        self.client.force_login(self.bob)

        response = self.client.post(f"/community/post/{self.post.id}/delete/")

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_sidebar_shows_moderation_only_to_admin(self):
        self.client.force_login(self.alice)
        self.assertNotContains(self.client.get("/community/"), "/community/moderation/")

        self.client.force_login(self.admin)
        self.assertContains(self.client.get("/community/"), "/community/moderation/")



@override_settings(STORAGES=SIMPLE_STORAGES)
class SearchTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.alice = user_model.objects.create_user(username="alsashimi", password="test-password")
        self.bob = user_model.objects.create_user(username="bob", password="test-password")
        self.linen_post = Post.objects.create(author=self.alice, content="My new linen shirt for campus")
        self.jeans_post = Post.objects.create(author=self.bob, content="Wide jeans all week")
        self.url = "/community/search/"

    def test_empty_query_goes_back_to_feed(self):
        response = self.client.get(self.url, {"q": "   "})
        self.assertRedirects(response, "/community/")

    def test_finds_posts_by_content(self):
        response = self.client.get(self.url, {"q": "LINEN"})
        self.assertContains(response, "My new linen shirt")
        self.assertNotContains(response, "Wide jeans")
        self.assertContains(response, "Results for &ldquo;LINEN&rdquo;")

    def test_finds_posts_by_tagged_closet_item(self):
        item = Item.objects.create(user=self.bob, name="Kebaya brokat", category="top", color="red")
        self.jeans_post.tagged_items.add(item)
        response = self.client.get(self.url, {"q": "kebaya"})
        self.assertContains(response, "Wide jeans all week")

    def test_post_with_two_matching_tags_shows_once(self):
        for name in ("Linen pants", "Linen scarf"):
            self.linen_post.tagged_items.add(
                Item.objects.create(user=self.alice, name=name, category="bottom", color="beige")
            )
        response = self.client.get(self.url, {"q": "linen"})
        self.assertEqual(len(response.context["results"]), 1)

    def test_people_tab_finds_usernames(self):
        response = self.client.get(self.url, {"q": "alsa", "tab": "people"})
        self.assertContains(response, "@alsashimi")
        self.assertNotContains(response, "@bob")

    def test_at_sign_opens_people_tab(self):
        response = self.client.get(self.url, {"q": "@alsashimi"})
        self.assertEqual(response.context["tab"], "people")
        self.assertContains(response, "@alsashimi")

    def test_no_results_shows_ask_button(self):
        self.client.login(username="bob", password="test-password")
        response = self.client.get(self.url, {"q": "kebaya modern"})
        self.assertContains(response, "No results for “kebaya modern”")
        self.assertContains(response, "/community/?ask=kebaya+modern#composer")

    def test_ask_link_fills_the_composer(self):
        self.client.login(username="bob", password="test-password")
        response = self.client.get("/community/", {"ask": "kebaya modern"})
        self.assertContains(response, ">kebaya modern</textarea>")

    def test_navbar_search_points_to_search_page(self):
        self.client.login(username="bob", password="test-password")
        response = self.client.get(self.url, {"q": "linen"})
        self.assertContains(response, 'action="/community/search/"')
        self.assertContains(response, 'value="linen"')

