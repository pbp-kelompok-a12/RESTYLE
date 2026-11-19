from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from closet.models import Item
from .api_serializers import ClosetItemSerializer


class ClosetItemListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ClosetItemSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClosetItemDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClosetItemSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)
