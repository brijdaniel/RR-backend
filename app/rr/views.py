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
    queryset = Checklist.objects.all()
    serializer_class = ChecklistSerializer


class RegretListCreateView(ListCreateAPIView):
    queryset = Regret.objects.all()
    serializer_class = RegretSerializer


class RegretRetrieveUpdateView(RetrieveUpdateAPIView):
    queryset = Regret.objects.all()
    serializer_class = RegretSerializer
    lookup_field = "id"
