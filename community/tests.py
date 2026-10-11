from django.contrib.auth import get_user_model
from django.test import TestCase

from community.models import Comment, Follow, Post


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
