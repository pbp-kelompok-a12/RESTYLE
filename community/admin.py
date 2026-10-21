from django.contrib import admin

from community.models import Comment, CommunityProfile, Follow, Notification, Post, PostImage


class PostImageInline(admin.TabularInline):
    # foto-foto post tampil langsung di halaman detail post
    model = PostImage
    extra = 0

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "content", "created_at")
    search_fields = ("content", "author__username")
    list_filter = ("created_at",)
    date_hierarchy = "created_at"
    inlines = [PostImageInline]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "parent", "content", "created_at")
    search_fields = ("content", "author__username")
    list_filter = ("created_at",)

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followed", "created_at")
    search_fields = ("follower__username", "followed__username")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "actor", "kind", "is_read", "created_at")
    list_filter = ("kind", "is_read")

admin.site.register(CommunityProfile)