from django.conf import settings
from django.db import models
from django.utils import timezone


def short_time_ago(moment):
    """change waktu jd teks pendek, misalnya '2h ago'."""
    seconds = int((timezone.now() - moment).total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    if seconds < 604800:
        return f"{seconds // 86400}d ago"
    return moment.strftime("%d %b %Y")


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )
    content = models.TextField(max_length=1000)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_posts",
        blank=True,
    )
    saved_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="saved_posts",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"@{self.author.username}: {self.content[:40]}"

    @property
    def time_ago(self):
        return short_time_ago(self.created_at)

    @property
    def top_level_comments(self):
        # comment langsung ke post (bukan balasan ke komentar lain).
        return self.comments.filter(parent__isnull=True)


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )
    content = models.TextField(max_length=500)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_comments",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"@{self.author.username}: {self.content[:40]}"

    @property
    def time_ago(self):
        return short_time_ago(self.created_at)

    @property
    def is_author(self):
        # true kalau yang komen tuh yang bikin post.
        return self.author_id == self.post.author_id