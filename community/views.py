from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Exists, OuterRef
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from community.forms import CommentForm, PostForm
from community.models import Comment, Follow, Post, PostImage

# URL halaman login aplikasi.
LOGIN_URL = "/login/"

MAX_PHOTOS = 3
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_PHOTO_TYPES = ["image/jpeg", "image/png"]

def show_community(request):
    # tab yang sedang dibuka: "for-you" (semua post) atau "following".
    tab = request.GET.get("tab", "for-you")

    posts = Post.objects.select_related("author")
    if tab == "following":
        if not request.user.is_authenticated:
            return redirect(LOGIN_URL)
        # Hanya post dari orang yang diikuti user ini.
        posts = posts.filter(author__follower_links__follower=request.user)

    # tiga post dengan like terbanyak dalam 7 hari terakhir.
    one_week_ago = timezone.now() - timedelta(days=7)
    popular_posts = (
        Post.objects.filter(created_at__gte=one_week_ago)
        .annotate(like_count=Count("likes"))
        .order_by("-like_count", "-created_at")[:3]
    )

    # saran orang untuk diikuti: bukan diri sendiri dan belum diikuti,
    # diurutkan dari yang paling banyak post-nya.
    following_ids = (
        Follow.objects.filter(follower=request.user).values_list("followed_id", flat=True)
        if request.user.is_authenticated
        else []
    )
    users = get_user_model().objects.all()
    if request.user.is_authenticated:
        users = users.exclude(id=request.user.id)
    stylists = (
        users.exclude(id__in=following_ids)
        .annotate(post_count=Count("community_posts"))
        .order_by("-post_count", "username")[:4]
    )

    following_people = (
        get_user_model().objects.filter(id__in=following_ids).order_by("username")
        if request.user.is_authenticated
        else []
    )

    context = {
        "tab": tab,
        "posts": posts,
        "popular_posts": popular_posts,
        "stylists": stylists,
        "following_people": following_people,
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

def toggle_user(relation, user):
    """Menambahkan user ke sebuah daftar (like atau saved) kalau belum ada,
    dan mengeluarkannya kalau sudah ada. Mengembalikan True kalau sekarang ada."""
    if relation.filter(id=user.id).exists():
        relation.remove(user)
        return False
    relation.add(user)
    return True

@login_required(login_url=LOGIN_URL)
@require_POST
def toggle_post_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_liked = toggle_user(post.likes, request.user)
    return JsonResponse({"active": is_liked, "count": post.likes.count()})


@login_required(login_url=LOGIN_URL)
@require_POST
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    is_liked = toggle_user(comment.likes, request.user)
    return JsonResponse({"active": is_liked, "count": comment.likes.count()})

@login_required(login_url=LOGIN_URL)
@require_POST
def toggle_post_save(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_saved = toggle_user(post.saved_by, request.user)
    return JsonResponse({"active": is_saved})

@login_required(login_url=LOGIN_URL)
def show_saved(request):
    posts = request.user.saved_posts.select_related("author")
    return render(request, "community/saved.html", {"posts": posts})

def show_user_profile(request, username):
    profile_user = get_object_or_404(get_user_model(), username=username)
    posts = (
        Post.objects.filter(author=profile_user)
        .select_related("author")
        .prefetch_related("images")
    )
    is_following = (
        Follow.objects.filter(
            follower=request.user,
            followed=profile_user,
        ).exists()
        if request.user.is_authenticated
        else False
    )

    context = {
        "profile_user": profile_user,
        "posts": posts,
        "following_count": profile_user.following_links.count(),
        "followers_count": profile_user.follower_links.count(),
        "is_following": is_following,
    }
    if profile_user == request.user:
        from main.models import UserProfile

        context["profile"] = UserProfile.objects.get_or_create(user=request.user)[0]

    return render(
        request,
        "community/profile.html",
        context,
    )

def show_follow_list(request, username, list_type):
    profile_user = get_object_or_404(get_user_model(), username=username)

    if list_type == "following":
        people = get_user_model().objects.filter(
            follower_links__follower=profile_user,
        )
        title = "Following"
    else:
        people = get_user_model().objects.filter(
            following_links__followed=profile_user,
        )
        title = "Followers"

    if request.user.is_authenticated:
        people = people.annotate(
            is_following=Exists(
                Follow.objects.filter(
                    follower=request.user,
                    followed_id=OuterRef("pk"),
                )
            )
        )
    people = people.order_by("username")

    return render(
        request,
        "community/follow_list.html",
        {
            "profile_user": profile_user,
            "people": people,
            "list_type": list_type,
            "title": title,
        },
    )

@login_required(login_url=LOGIN_URL)
@require_POST
def toggle_follow(request, username):
    target = get_object_or_404(get_user_model(), username=username)
    if target == request.user:
        return JsonResponse({"error": "You can't follow yourself."}, status=400)

    link = Follow.objects.filter(follower=request.user, followed=target)
    if link.exists():
        link.delete()
        is_following = False
    else:
        Follow.objects.create(follower=request.user, followed=target)
        is_following = True

    return JsonResponse({"active": is_following})
