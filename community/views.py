from datetime import timedelta

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from community.models import Post

# masih data contoh. ntar diganti data asli kalo fitur follow udah dibuat.
DUMMY_STYLISTS = [
    {"username": "ailuavihs", "bio": "Layering ideas"},
    {"username": "hasya.jpeg", "bio": "1 piece, 3 ways"},
    {"username": "fadly.rewears", "bio": "Thrift finds"},
    {"username": "sakhiwears", "bio": "Fashion girlie"},
]


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