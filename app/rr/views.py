from rest_framework.generics import RetrieveAPIView, CreateAPIView, ListCreateAPIView, ListAPIView, RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView
from rest_framework.exceptions import ValidationError
from django_filters import rest_framework as filters
import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import *
from .serializers import *
from .filters import ChecklistFilter
from rest_framework.permissions import IsAdminUser, IsAuthenticated

logger = logging.getLogger(__name__)

class UserCreateView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = []  # Allow anyone to register

    def perform_create(self, serializer):
        logger.info("About to create user")
        user = serializer.save()
        logger.info(f"User created with is_active = {user.is_active}")
        return user


class ChecklistListCreateView(ListAPIView):
    serializer_class = ChecklistSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ChecklistFilter
    filter_backends = (filters.DjangoFilterBackend,)

    def get_queryset(self):
        return Checklist.objects.filter(user=self.request.user)


class RegretListCreateView(ListCreateAPIView):
    serializer_class = RegretSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Regret.objects.filter(checklist__user=self.request.user, checklist__id=self.kwargs["pk"])
    
    def perform_create(self, serializer):
        checklist = get_object_or_404(Checklist, pk=self.kwargs["pk"], user=self.request.user)
        serializer.save(checklist=checklist)


class RegretRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = RegretSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Regret.objects.filter(checklist__user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        # Only allow updates if it is the same day the checklist was created
        regret = self.get_object()
        if regret.checklist.created_at.date() != timezone.now().date():
            raise ValidationError("Too late, the regret is real!")
        
        # Only allow success field to be updated from false to true
        mutable_data = request.data.copy()
        allowed_keys = {'success'}
        for key in list(mutable_data.keys()):
            if key not in allowed_keys:
                del mutable_data[key]

        # Check if trying to update success field
        if 'success' in mutable_data:
            # Only allow updating from false to true
            if regret.success:
                raise ValidationError("Cannot undo a successful regret resolution!")
            if not mutable_data['success']:
                raise ValidationError("Can only update success from false to true!")

        request._full_data = mutable_data  # Forces DRF to use this cleaned data
        return super().update(request, *args, **kwargs)
