from django.conf import settings
from django.db import models
from django.urls import reverse
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
    # pakaian dari Digital Closet yang dipakai di post ini
    tagged_items = models.ManyToManyField(
        "closet.Item",
        related_name="community_posts",
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
    # reply boleh membawa satu foto dan pakaian dari closet, misalnya untuk menyarankan outfit
    photo = models.ImageField(upload_to="community/comments/", blank=True)
    tagged_items = models.ManyToManyField(
        "closet.Item",
        related_name="community_comments",
        blank=True,
    )
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
    
class PostImage(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="community/posts/")

    def __str__(self):
        return f"Photo for post {self.post_id}"

class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_links",
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "followed"], name="unique_follow"),
        ]

    def __str__(self):
        return f"@{self.follower.username} follows @{self.followed.username}"
    
class Notification(models.Model):
    REPLY = "reply"
    LIKE = "like"
    FOLLOW = "follow"
    MENTION = "mention"
    KIND_CHOICES = [
        (REPLY, "Reply"),
        (LIKE, "Like"),
        (FOLLOW, "Follow"),
        (MENTION, "Mention"),
    ]

    # yang menerima notifikasi
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    # yang melakukan aksinya (yang membalas, nge-like, atau nge-follow)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"@{self.actor.username} -> @{self.recipient.username}: {self.kind}"

    @property
    def time_ago(self):
        seconds = (timezone.now() - self.created_at).total_seconds()
        if 86400 <= seconds < 172800:
            return "Yesterday"
        return short_time_ago(self.created_at)

    @property
    def other_likes(self):
        # jumlah orang lain (selain actor dan pemilik post) yang juga nge-like post ini
        return self.post.likes.exclude(id__in=[self.actor_id, self.recipient_id]).count()

    @property
    def message(self):
        """kalimat notifikasi tanpa username actor, misalnya 'liked your post'."""
        if self.kind == self.FOLLOW:
            return "started following you"
        if self.kind == self.LIKE:
            others = self.other_likes
            if others:
                return f"and {others} other{'s' if others > 1 else ''} liked your post"
            return "liked your post"
        if self.kind == self.MENTION:
            # disebut di reply (ada comment) atau di post-nya sendiri
            text = self.comment.content if self.comment_id else self.post.content
            preview = text if len(text) <= 40 else text[:40] + "…"
            where = "a reply" if self.comment_id else "a post"
            return f"mentioned you in {where}: “{preview}”"
        target = "your post" if self.recipient_id == self.post.author_id else "your comment"
        preview = self.comment.content if len(self.comment.content) <= 40 else self.comment.content[:40] + "…"
        return f"replied to {target}: “{preview}”"

    @property
    def target_url(self):
        """halaman yang dibuka saat notifikasi diklik."""
        if self.kind == self.FOLLOW:
            return reverse("community:show_user_profile", args=[self.actor.username])
        return reverse("community:show_community") + f"#post-{self.post_id}"
    
class CommunityProfile(models.Model):
    """data tambahan user khusus untuk community, misalnya foto profil."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_profile",
    )
    photo = models.ImageField(upload_to="community/avatars/", blank=True)

    def __str__(self):
        return f"Community profile of @{self.user.username}"