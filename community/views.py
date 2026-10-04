from django.shortcuts import render

# Data contoh (dummy). Di langkah 3 ini diganti dengan data asli dari database.
DUMMY_POSTS = [
    {
        "username": "ailuavihs",
        "time": "2h ago",
        "content": (
            "guys white shirt + jeans buat kelas jam 7 tuh basic banget ga sih 😭\n\n"
            "pengen yang nyaman soalnya masih ngantuk, tapi kayaknya tiap minggu gw "
            "pake outfit ini lagi. ada ide styling pake baju yang udah ada ga?"
        ),
        "likes": 24,
        "reply_count": 8,
        "more_replies": 4,
        "tagged_items": [
            {"name": "Layered sweater", "image": "/static/img/layered_sweater.png"},
            {"name": "Wrap jeans", "image": "/static/img/wrap_jeans.png"},
        ],
        "comments": [
            {
                "username": "alsashimi",
                "time": "1h ago",
                "content": "engga kok 😭 coba tambah cardigan beige + sneakers. kemejanya juga coba masukin setengah aja biar ga keliatan terlalu formal",
                "likes": 14,
                "replies": [
                    {
                        "username": "ailuavihs",
                        "time": "45m ago",
                        "content": "OHH gw punya cardigan beige yang kayaknya belum pernah dipake deh okkkk besok gw coba",
                        "likes": 3,
                        "is_author": True,
                    },
                    {
                        "username": "fadly.rewears",
                        "time": "30m ago",
                        "content": "sleeves-nya digulung 2× terus pake belt tipis juga lucu sih.",
                        "likes": 5,
                    },
                ],
            },
            {
                "username": "hasya.jpeg",
                "time": "1h ago",
                "content": "kalo kelasnya dingin parah, ganti cardigan pake denim outer. masuk juga sama jeansnya",
                "likes": 14,
            },
            {
                "username": "sakhiwears",
                "time": "1h ago",
                "content": "ternyata kita bukan butuh baju baru ya, butuh ide baru",
                "likes": 14,
            },
        ],
    },
    {
        "username": "lalalostyou",
        "time": "2h ago",
        "content": "guys ada ga cara bikin kaos yang udah sering dipake keliatan beda .. bosen liat diri sendiri pake itu terus",
        "likes": 24,
        "reply_count": 8,
    },
]

DUMMY_POPULAR = [
    {"title": "Soft-blue week: my palette for October", "likes": 56},
    {"title": "One linen shirt, three campus looks", "likes": 41},
    {"title": "Does a white shirt and jeans feel too basic?", "likes": 24},
]

DUMMY_STYLISTS = [
    {"username": "ailuavihs", "bio": "Layering ideas"},
    {"username": "hasya.jpeg", "bio": "1 piece, 3 ways"},
    {"username": "fadly.rewears", "bio": "Thrift finds"},
    {"username": "sakhiwears", "bio": "Fashion girlie"},
]


def show_community(request):
    context = {
        "posts": DUMMY_POSTS,
        "popular_posts": DUMMY_POPULAR,
        "stylists": DUMMY_STYLISTS,
    }
    return render(request, "community/feed.html", context)