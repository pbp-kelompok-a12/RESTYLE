from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from community.forms import CommentForm, PostForm
from community.models import Comment, Post, PostImage

# sementara login lewat halaman admin dulu, ntar ganti kalau halaman login modul 4 udah ada
LOGIN_URL = "/admin/login/"

MAX_PHOTOS = 3
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_PHOTO_TYPES = ["image/jpeg", "image/png"]

# masih data contoh. ntar diganti data asli kalo fitur follow udah dibuat.
DUMMY_STYLISTS = [
    {"username": "ailuavihs", "bio": "Layering ideas"},
    {"username": "hasya.jpeg", "bio": "1 piece, 3 ways"},
    {"username": "fadly.rewears", "bio": "Thrift finds"},
    {"username": "sakhiwears", "bio": "Fashion girlie"},
]

@login_required(login_url=LOGIN_URL)
def show_community(request):
    # semua post, yang terbaru di atas.
    posts = Post.objects.select_related("author")

    # tiga post like terbanyak dalam 7 hari terakhir.
    one_week_ago = timezone.now() - timedelta(days=7)
    popular_posts = (
        Post.objects.filter(created_at__gte=one_week_ago)
        .annotate(like_count=Count("likes"))
        .order_by("-like_count", "-created_at")[:3]
    )

    context = {
        "posts": posts,
        "popular_posts": popular_posts,
        "stylists": DUMMY_STYLISTS,
    }
    return render(request, "community/feed.html", context)

def check_photos(photos):
    """return pesan error kalau ada foto yang bermasalah, atau None kalau aman"""
    if len(photos) > MAX_PHOTOS:
        return f"You can add up to {MAX_PHOTOS} photos per post."

    for photo in photos:
        if photo.size > MAX_PHOTO_SIZE:
            return "Each photo must be 5 MB or smaller."
        try:
            forms.ImageField().clean(photo)  # memastikan file ini benar-benar gambar
        except ValidationError:
            return "Photos must be JPG or PNG images."
        if photo.content_type not in ALLOWED_PHOTO_TYPES:
            return "Photos must be JPG or PNG images."

    return None

@login_required(login_url=LOGIN_URL)
@require_POST
def create_post(request):
    form = PostForm(request.POST)
    photos = request.FILES.getlist("photos")

    if not form.is_valid():
        messages.error(request, "Write something before posting (up to 1000 characters).")
        return redirect("community:show_community")

    photo_error = check_photos(photos)
    if photo_error:
        messages.error(request, photo_error)
        return redirect("community:show_community")

    post = form.save(commit=False)  # belum disimpan, karena authornya belum diisi
    post.author = request.user
    post.save()

    for photo in photos:
        PostImage.objects.create(post=post, image=photo)

    messages.success(request, "Your post is live.")
    return redirect("community:show_community")



@login_required(login_url=LOGIN_URL)
@require_POST
def create_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user

        parent_id = request.POST.get("parent", "")
        if parent_id.isdigit():
            parent = get_object_or_404(Comment, id=parent_id, post=post)
            # balasan untuk sebuah balasan ditempelkan ke komentar utamanya,
            # supaya balasan cuma menjorok satu tingkat
            comment.parent = parent.parent or parent

        comment.save()
    else:
        messages.error(request, "Write a reply before sending (up to 500 characters).")

    # balik ke feed, langsung ke post yang dikomentari
    return redirect(reverse("community:show_community") + f"#post-{post.id}")

def feed_url(post_id):
    """Alamat feed yang langsung melompat ke satu post."""
    return reverse("community:show_community") + f"#post-{post_id}"

@login_required(login_url=LOGIN_URL)
@require_POST
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return HttpResponseForbidden("You can only edit your own posts.")

    form = PostForm(request.POST, instance=post)
    if not form.is_valid():
        messages.error(request, "A post can't be empty (up to 1000 characters).")
        return redirect("community:show_community")

    form.save()
    return redirect(feed_url(post.id))

@login_required(login_url=LOGIN_URL)
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You can only delete your own posts.")

    post.delete()
    messages.success(request, "Post deleted.")
    return redirect("community:show_community")

@login_required(login_url=LOGIN_URL)
@require_POST
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return HttpResponseForbidden("You can only edit your own replies.")

    form = CommentForm(request.POST, instance=comment)
    if not form.is_valid():
        messages.error(request, "A reply can't be empty (up to 500 characters).")
        return redirect("community:show_community")

    form.save()
    return redirect(feed_url(comment.post_id))

@login_required(login_url=LOGIN_URL)
@require_POST
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return HttpResponseForbidden("You can only edit your own replies.")

    form = CommentForm(request.POST, instance=comment)
    if not form.is_valid():
        messages.error(request, "A reply can't be empty (up to 500 characters).")
        return redirect("community:show_community")

    form.save()
    return redirect(feed_url(comment.post_id))

@login_required(login_url=LOGIN_URL)
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You can only delete your own replies.")

    post_id = comment.post_id
    comment.delete()
    return redirect(feed_url(post_id))