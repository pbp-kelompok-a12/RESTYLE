
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Post
from .serializers import PostSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def post_list_api(request):
    posts = (
        Post.objects
        .select_related("author")
        .prefetch_related("likes", "comments")
        .all()[:50]
    )

    serializer = PostSerializer(
        posts,
        many=True,
        context={"request": request},
    )

    return Response({
        "posts": serializer.data,
    })
