from rest_framework import viewsets
from rest_framework.generics import RetrieveAPIView, CreateAPIView, ListCreateAPIView, ListAPIView, RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView
from .models import *
from .serializers import *
from rest_framework.permissions import IsAdminUser


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class ChecklistListCreateView(ListCreateAPIView):
    serializer_class = ChecklistSerializer

    def get_queryset(self):
        return Checklist.objects.filter(user=self.request.user)


class RegretListCreateView(ListCreateAPIView):
    serializer_class = RegretSerializer

    def get_queryset(self):
        return Regret.objects.filter(checklist__user=self.request.user)


class RegretRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = RegretSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Regret.objects.filter(checklist__user=self.request.user)
