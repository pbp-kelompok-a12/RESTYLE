from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_POST

from community.forms import CommentForm, PostForm
from closet.models import Item
from community.models import Comment, CommunityProfile, Follow, Notification, Post, PostImage
from community.notifications import (
    notify_follow,
    notify_like,
    notify_mentions,
    notify_reply,
    undo_follow,
    undo_like,
)
from restyle.image_processing import optimize_image_upload

# URL halaman login aplikasi.
LOGIN_URL = "/login/"

MAX_PHOTOS = 3
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_TAGS = 5

def show_community(request):
    # tab yang sedang dibuka: "for-you" (semua post) atau "following".
    tab = request.GET.get("tab", "for-you")

    posts = Post.objects.select_related("author").prefetch_related("images", "tagged_items")    
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

    # angka kecil di banner atas
    hero_stats = [
        ("Posts this week", Post.objects.filter(created_at__gte=one_week_ago).count()),
        ("Members", get_user_model().objects.count()),
        ("Outfits tagged", Post.objects.filter(tagged_items__isnull=False).distinct().count()),
    ]

    context = {
        "tab": tab,
        "posts": posts,
        "popular_posts": popular_posts,
        "stylists": stylists,
        "following_people": following_people,
        "hero_stats": hero_stats,
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

def pick_tagged_items(request):
    """ambil item closet yang dicentang, tapi hanya yang benar-benar milik user ini"""
    item_ids = [item_id for item_id in request.POST.getlist("tagged_items") if item_id.isdigit()]
    return Item.objects.filter(user=request.user, id__in=item_ids)

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

    tagged_items = pick_tagged_items(request)
    if tagged_items.count() > MAX_TAGS:
        messages.error(request, f"You can tag up to {MAX_TAGS} closet items per post.")
        return redirect("community:show_community")
    
    post = form.save(commit=False)  # belum disimpan, karena authornya belum diisi
    post.author = request.user
    post.save()
    post.tagged_items.set(tagged_items)

    for photo in photos:
        PostImage.objects.create(post=post, image=optimize_image_upload(photo))

    notify_mentions(request.user, post)
    messages.success(request, "Your post is live.")
    return redirect("community:show_community")



@login_required(login_url=LOGIN_URL)
@require_POST
def create_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    back_to_post = redirect(reverse("community:show_community") + f"#post-{post.id}")

    # foto (maksimal satu) dan pakaian dari closet yang ikut dikirim bersama reply
    photo = request.FILES.get("photo")
    photo_error = check_photos([photo]) if photo else None
    if photo_error:
        messages.error(request, photo_error)
        return back_to_post

    tagged_items = pick_tagged_items(request)
    if tagged_items.count() > MAX_TAGS:
        messages.error(request, f"You can tag up to {MAX_TAGS} closet items per reply.")
        return back_to_post

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

        if photo:
            comment.photo = optimize_image_upload(photo)
        comment.save()
        comment.tagged_items.set(tagged_items)
        replied = notify_reply(comment)
        notify_mentions(request.user, post, comment=comment, skip=replied)
    else:
        messages.error(request, "Write a reply before sending (up to 500 characters).")

    # balik ke feed, langsung ke post yang dikomentari
    return back_to_post

def redirect_back(request, fallback):
    """kembali ke halaman asal (dikirim lewat input "next"), kalau alamatnya aman."""
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect(fallback)

def feed_url(post_id):
    """Alamat feed yang langsung melompat ke satu post."""
    return reverse("community:show_community") + f"#post-{post_id}"

@login_required(login_url=LOGIN_URL)
@require_POST
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return HttpResponseForbidden("You can only edit your own posts.")

    old_content = post.content  # disimpan dulu: form.is_valid() langsung mengubah isi post
    form = PostForm(request.POST, instance=post)
    if not form.is_valid():
        messages.error(request, "A post can't be empty (up to 1000 characters).")
        return redirect(feed_url(post.id))

    # foto lama yang ditandai untuk dihapus, dan foto baru yang ditambahkan
    remove_ids = [photo_id for photo_id in request.POST.getlist("remove_photos") if photo_id.isdigit()]
    photos_to_remove = post.images.filter(id__in=remove_ids)
    new_photos = request.FILES.getlist("photos")

    # jumlah foto setelah diedit = foto lama - yang dihapus + foto baru
    photo_total = post.images.count() - photos_to_remove.count() + len(new_photos)
    if photo_total > MAX_PHOTOS:
        messages.error(request, f"You can add up to {MAX_PHOTOS} photos per post.")
        return redirect(feed_url(post.id))

    photo_error = check_photos(new_photos)
    if photo_error:
        messages.error(request, photo_error)
        return redirect(feed_url(post.id))

    tagged_items = pick_tagged_items(request)
    if tagged_items.count() > MAX_TAGS:
        messages.error(request, f"You can tag up to {MAX_TAGS} closet items per post.")
        return redirect(feed_url(post.id))

    form.save()
    post.tagged_items.set(tagged_items)
    photos_to_remove.delete()    
    
    for photo in new_photos:
        PostImage.objects.create(post=post, image=optimize_image_upload(photo))

    notify_mentions(request.user, post, old_text=old_content)
    messages.success(request, "Your post was updated.")
    return redirect(feed_url(post.id))

@login_required(login_url=LOGIN_URL)
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You can only delete your own posts.")

    post.delete()
    messages.success(request, "Post deleted.")
    return redirect_back(request, "community:show_community")

@login_required(login_url=LOGIN_URL)
@require_POST
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return HttpResponseForbidden("You can only edit your own replies.")

    old_content = comment.content  # disimpan dulu: form.is_valid() langsung mengubah isi reply
    form = CommentForm(request.POST, instance=comment)
    if not form.is_valid():
        messages.error(request, "A reply can't be empty (up to 500 characters).")
        return redirect("community:show_community")

    form.save()
    notify_mentions(request.user, comment.post, comment=comment, old_text=old_content)
    messages.success(request, "Your reply was updated.")
    return redirect(feed_url(comment.post_id))

@login_required(login_url=LOGIN_URL)
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You can only delete your own replies.")

    post_id = comment.post_id
    comment.delete()
    messages.success(request, "Reply deleted.")
    return redirect_back(request, feed_url(post_id))

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
    if is_liked:
        notify_like(post, request.user)
    else:
        undo_like(post, request.user)
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
        undo_follow(request.user, target)
        is_following = False
    else:
        Follow.objects.create(follower=request.user, followed=target)
        notify_follow(request.user, target)
        is_following = True

    return JsonResponse({"active": is_following})

@login_required(login_url=LOGIN_URL)
def show_notifications(request):
    notifications = request.user.notifications.select_related("actor", "post", "comment")[:50]
    has_unread = request.user.notifications.filter(is_read=False).exists()
    return render(
        request,
        "community/notifications.html",
        {"notifications": notifications, "has_unread": has_unread},
    )

@login_required(login_url=LOGIN_URL)
def open_notification(request, notification_id):
    # notifikasi yang diklik ditandai sudah dibaca, lalu langsung ke post/profil terkait
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect(notification.target_url)

@login_required(login_url=LOGIN_URL)
@require_POST
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"ok": True})
    return redirect("community:show_notifications")

@login_required(login_url=LOGIN_URL)
@require_POST
def update_avatar(request):
    profile, _ = CommunityProfile.objects.get_or_create(user=request.user)
    profile_url = reverse("community:show_user_profile", args=[request.user.username])

    if "remove" in request.POST:
        profile.photo.delete(save=False)
        profile.photo = ""
        profile.save()
        messages.success(request, "Profile photo removed.")
        return redirect(profile_url)

    photo = request.FILES.get("photo")
    if photo is None:
        messages.error(request, "Choose a photo first.")
        return redirect(profile_url)

    photo_error = check_photos([photo])
    if photo_error:
        messages.error(request, photo_error.replace("Each photo", "Your photo"))
        return redirect(profile_url)

    if profile.photo:
        profile.photo.delete(save=False)  # buang foto lama supaya tidak menumpuk
    profile.photo = optimize_image_upload(photo)
    profile.save()
    messages.success(request, "Profile photo updated.")
    return redirect(profile_url)

@login_required(login_url=LOGIN_URL)
def show_moderation(request):
    """halaman admin: lihat semua post/komentar, cari, lalu hapus yang melanggar."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Only admins can open this page.")

    tab = request.GET.get("tab", "posts")
    query = request.GET.get("q", "").strip()

    if tab == "comments":
        items = Comment.objects.select_related("author", "post").prefetch_related("tagged_items")
    else:
        tab = "posts"
        items = Post.objects.select_related("author").prefetch_related("images").annotate(
            reply_count=Count("comments", distinct=True),
            like_count=Count("likes", distinct=True),
            photo_count=Count("images", distinct=True),
        )

    if query:
        # cari di isi tulisan atau username penulisnya
        items = items.filter(Q(content__icontains=query) | Q(author__username__icontains=query))

    page = Paginator(items.order_by("-created_at"), 20).get_page(request.GET.get("page"))

    one_day_ago = timezone.now() - timedelta(days=1)
    # (label, angka, ikon Font Awesome)
    stats = [
        ("Posts", Post.objects.count(), "fa-regular fa-images"),
        ("Replies", Comment.objects.count(), "fa-regular fa-comments"),
        ("New posts today", Post.objects.filter(created_at__gte=one_day_ago).count(), "fa-solid fa-bolt"),
        ("Members", get_user_model().objects.count(), "fa-solid fa-user-group"),
    ]

    return render(
        request,
        "community/moderation.html",
        {"tab": tab, "query": query, "page": page, "stats": stats, "one_day_ago": one_day_ago},
    )

def show_search(request):
    """hasil pencarian dari kotak search di navbar: tab Posts atau People."""
    query = request.GET.get("q", "").strip()
    if not query:
        return redirect("community:show_community")

    # "@alsashimi" dicari sebagai username, jadi tanda @ dibuang dulu
    word = query.lstrip("@") or query
    tab = request.GET.get("tab", "people" if query.startswith("@") else "posts")

    if tab == "people":
        results = (
            get_user_model().objects.filter(
                Q(username__icontains=word) | Q(first_name__icontains=word) | Q(last_name__icontains=word)
            )
            .annotate(post_count=Count("community_posts"))
            .order_by("-post_count", "username")
        )
        if request.user.is_authenticated:
            results = results.annotate(
                is_following=Exists(Follow.objects.filter(follower=request.user, followed_id=OuterRef("pk")))
            )
    else:
        tab = "posts"
        # cocok kalau kata itu ada di isi post, username penulis, atau item closet yang di-tag
        results = (
            Post.objects.filter(
                Q(content__icontains=word)
                | Q(author__username__icontains=word)
                | Q(tagged_items__name__icontains=word)
                | Q(tagged_items__material__icontains=word)
                | Q(tagged_items__category__icontains=word)
            )
            .distinct()
            .select_related("author")
            .prefetch_related("images", "tagged_items")
        )

    # tombol "Ask the community" membuka kotak tulis post yang sudah berisi kata yang dicari
    if request.user.is_authenticated:
        ask_url = reverse("community:show_community") + "?" + urlencode({"ask": query}) + "#composer"
    else:
        ask_url = LOGIN_URL

    context = {
        "query": query,
        "tab": tab,
        "results": results,
        "empty_title": f"No results for “{query}”",
        "ask_url": ask_url,
    }
    return render(request, "community/search.html", context)


@login_required(login_url=LOGIN_URL)
def mention_suggestions(request):
    """saran username saat mengetik @ di kotak tulis: yang depannya cocok dulu, maksimal 6."""
    query = request.GET.get("q", "").strip().lstrip("@")
    users = get_user_model().objects.exclude(id=request.user.id).select_related("community_profile")
    if query:
        users = users.filter(username__icontains=query)
    users = sorted(users[:30], key=lambda user: (not user.username.lower().startswith(query.lower()), user.username.lower()))[:6]

    results = []
    for user in users:
        profile = getattr(user, "community_profile", None)
        results.append({
            "username": user.username,
            "photo": profile.photo.url if profile and profile.photo else "",
        })
    return JsonResponse({"results": results})
