from rest_framework.generics import RetrieveAPIView, CreateAPIView, ListCreateAPIView, ListAPIView, RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView
from rest_framework.exceptions import ValidationError
from django_filters import rest_framework as filters
import logging
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime
import pytz

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

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
        print("About to create user")
        user = serializer.save()
        print(f"User created with is_active = {user.is_active}")
        return user


class ChecklistListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's checklists with filtering"""
        checklists = Checklist.objects.filter(user=request.user)
        serializer = ChecklistSerializer(checklists, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create or get checklist for the specified local datetime"""
        user = request.user
        local_datetime_str = request.data.get('local_datetime')
        
        if not local_datetime_str:
            raise ValidationError("local_datetime is required")
        
        # Parse ISO datetime string
        try:
            # Django will automatically parse ISO format with timezone info
            local_datetime = datetime.fromisoformat(local_datetime_str.replace('Z', '+00:00'))
            if local_datetime.tzinfo is None:
                raise ValidationError("local_datetime must include timezone information")
        except ValueError:
            raise ValidationError("Invalid datetime format. Use ISO format with timezone (e.g., 2025-06-19T01:00:00+08:00)")
        
        # Convert to UTC for storage
        utc_datetime = local_datetime.astimezone(pytz.UTC)
        local_date = local_datetime.date()
        
        print(f"DEBUG: Checklist request - User: {user.username}, Request local: {local_datetime}, Request local date: {local_date}")
        
        # Get user's timezone from the local_datetime
        user_timezone = local_datetime.tzinfo
        
        # Check if checklist exists for this local date by converting stored UTC times to user's timezone
        user_checklists = Checklist.objects.filter(user=user)
        existing_checklist = None
        
        for checklist in user_checklists:
            # Convert checklist's UTC created_at to user's timezone
            checklist_local_date = checklist.created_at.astimezone(user_timezone).date()
            if checklist_local_date == local_date:
                existing_checklist = checklist
                print(f"DEBUG: Found checklist {checklist.id} - DB UTC: {checklist.created_at}, DB local: {checklist.created_at.astimezone(user_timezone)}")
                break
        
        if existing_checklist:
            # Return existing checklist
            serializer = ChecklistSerializer(existing_checklist)
            return Response(serializer.data)
        
        else:
            print(f"DEBUG: No checklist found for {local_date}, creating new one...")
            # Create new checklist
            with transaction.atomic():
                # Double-check after acquiring lock
                user_checklists = Checklist.objects.filter(user=user)
                existing_checklist = None
                
                for checklist in user_checklists:
                    checklist_local_date = checklist.created_at.astimezone(user_timezone).date()
                    if checklist_local_date == local_date:
                        existing_checklist = checklist
                        break
                
                if not existing_checklist:
                    try:
                        checklist = Checklist.objects.create(
                            user=user,
                            created_at=utc_datetime
                        )
                        print(f"DEBUG: Successfully created checklist: {checklist.id}")
                    except Exception as e:
                        print(f"DEBUG: Error creating checklist: {e}")
                        raise
                else:
                    print(f"DEBUG: Checklist was created by another process: {existing_checklist.id}")
                    checklist = existing_checklist
            
            serializer = ChecklistSerializer(checklist)
            return Response(serializer.data, status=201)


class RegretListCreateView(ListCreateAPIView):
    serializer_class = RegretSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Regret.objects.filter(checklist__user=self.request.user, checklist__id=self.kwargs["pk"])
    
    def get(self, request, *args, **kwargs):
        """Get regrets for a specific checklist"""
        checklist_id = self.kwargs["pk"]
        user = request.user
        regrets = self.get_queryset()
        
        serializer = self.get_serializer(regrets, many=True)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        """Create a new regret"""
        checklist_id = self.kwargs["pk"]
        user = request.user
        print(f"DEBUG: Regret create request - User: {user.username}, Checklist ID: {checklist_id}")
        
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        checklist = get_object_or_404(Checklist, pk=self.kwargs["pk"], user=self.request.user)
        regret = serializer.save(checklist=checklist)
        print(f"DEBUG: Created regret {regret.id} for checklist {checklist.id} - DB UTC: {checklist.created_at}")
        
        return regret


class RegretRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = RegretSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Regret.objects.filter(checklist__user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        # Only allow updates if it is the same local day the checklist was created
        regret = self.get_object()
        
        print(f"DEBUG: Regret update request - User: {request.user.username}, Regret ID: {regret.id}, Checklist DB UTC: {regret.checklist.created_at}")
        
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


class UserLoginOrRegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = []  # Allow anyone to access

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            raise ValidationError("Username is required")

        # Try to get existing user
        try:
            user = User.objects.get(username=username)
            # User exists, return their tokens
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            # User doesn't exist, create new user
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            return Response(serializer.data, status=201)
