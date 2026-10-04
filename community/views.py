from django.shortcuts import render


def show_community(request):
    dummy_posts = [
        {
            "username": "ailuavlhs",
            "time": "2h ago",
            "content": "guys white shirt + jeans buat kelas jam 7 tuh basic banget ga sih",
            "likes": 24,
            "replies": 8,
        },
        {
            "username": "lalalostyou",
            "time": "2h ago",
            "content": "guys ada ga cara bikin kaos yang udah sering dipake keliatan beda",
            "likes": 24,
            "replies": 8,
        },
    ]
    context = {"posts": dummy_posts}
    return render(request, "community/feed.html", context)