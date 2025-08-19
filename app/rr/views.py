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

from .models import User, Checklist, Regret, Network
from .serializers import *
from .filters import ChecklistFilter
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db import IntegrityError

# Date Format Requirements for checklist_created_at:
# Format: ISO 8601 with UTC timezone
# Example: "2025-08-17T18:00:00Z"
# Breakdown: YYYY-MM-DDTHH:mm:ssZ (Z = UTC/Zulu time)
# Must be a string, not datetime object
# Must include Z suffix for UTC timezone
# Must use T separator between date and time

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


class NetworkValidationView(APIView):
    """Validate username for network addition"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, username):
        """Check if username is valid for following"""
        if not username:
            return Response({"error": "Username is required"}, status=400)
        
        try:
            target_user = User.objects.get(username=username, is_active=True)
            
            # Check if user is trying to follow themselves
            if target_user == request.user:
                return Response({"error": "You cannot follow yourself"}, status=409)
            
            # Check if already following
            if Network.objects.filter(follower=request.user, following=target_user).exists():
                return Response({"error": "You are already following this user"}, status=409)
            
            # Check if target user allows networking
            if not target_user.allow_networking:
                return Response({"error": "This user has networking disabled"}, status=403)
            
            return Response({
                "username": target_user.username,
                "user_id": target_user.id,
                "allow_networking": target_user.allow_networking
            }, status=200)
            
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Exception as e:
            logger.error(f"Error validating username {username}: {e}")
            return Response({"error": "Network operation failed"}, status=500)


class NetworkFollowView(APIView):
    """Add user to network (Follow)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, username):
        """Follow a user"""
        if not username:
            return Response({"error": "Username is required"}, status=400)
        
        try:
            target_user = User.objects.get(username=username, is_active=True)
            
            # Check if user is trying to follow themselves
            if target_user == request.user:
                return Response({"error": "You cannot follow yourself"}, status=409)
            
            # Check if already following
            if Network.objects.filter(follower=request.user, following=target_user).exists():
                return Response({"error": "You are already following this user"}, status=409)
            
            # Check if target user allows networking
            if not target_user.allow_networking:
                return Response({"error": "This user has networking disabled"}, status=403)
            
            # Create network relationship
            network = Network.objects.create(follower=request.user, following=target_user)
            
            return Response({
                "message": f"Successfully followed {target_user.username}",
                "network_id": network.id,
                "following": target_user.username
            }, status=201)
            
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except IntegrityError:
            return Response({"error": "You are already following this user"}, status=409)
        except Exception as e:
            logger.error(f"Error following user {username}: {e}")
            return Response({"error": "Network operation failed"}, status=500)


class NetworkUnfollowView(APIView):
    """Remove user from network (Unfollow)"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, username):
        """Unfollow a user"""
        if not username:
            return Response({"error": "Username is required"}, status=400)
        
        try:
            target_user = User.objects.get(username=username, is_active=True)
            
            # Check if following relationship exists
            network = Network.objects.filter(follower=request.user, following=target_user).first()
            
            if not network:
                return Response({"error": "You are not following this user"}, status=404)
            
            # Delete network relationship
            network.delete()
            
            return Response({
                "message": f"Successfully unfollowed {target_user.username}"
            }, status=200)
            
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Exception as e:
            logger.error(f"Error unfollowing user {username}: {e}")
            return Response({"error": "Network operation failed"}, status=500)


class NetworkListView(APIView):
    """Get network users (Following/Followers list)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, list_type="following"):
        """Get following or followers list"""
        if list_type not in ["following", "followers"]:
            return Response({"error": "Invalid list type. Use 'following' or 'followers'"}, status=400)
        
        try:
            if list_type == "following":
                # Get users that the current user follows
                networks = Network.objects.filter(follower=request.user).select_related('following')
                users = [network.following for network in networks]
            else:
                # Get users that follow the current user
                networks = Network.objects.filter(following=request.user).select_related('follower')
                users = [network.follower for network in networks]
            
            user_data = []
            
            for user in users:
                try:
                    # Get the latest checklist for this user (regardless of date)
                    latest_checklist = user.user_checklists.order_by('-created_at').first()
                    
                    if latest_checklist:
                        # Send actual score and UTC creation timestamp
                        user_data.append({
                            "id": user.id,
                            "username": user.username,
                            "regret_index": float(latest_checklist.score),
                            "checklist_created_at": latest_checklist.created_at.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "followers_count": max(0, user.followers_count),
                            "following_count": max(0, user.following_count),
                            "date_joined": user.date_joined
                        })
                    else:
                        # User has no checklists at all - skip them
                        continue
                        
                except Exception as e:
                    logger.error(f"Error processing user {user.id} in network list: {e}")
                    # Skip problematic users but continue with others
                    continue
            
            return Response({
                "list_type": list_type,
                "count": len(user_data),
                "users": user_data
            }, status=200)
            
        except Exception as e:
            logger.error(f"Error getting {list_type} list: {e}")
            return Response({"error": "Network operation failed"}, status=500)


class NetworkSettingsView(APIView):
    """Update user's networking preferences"""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        """Update networking settings"""
        allow_networking = request.data.get('allow_networking')
        
        if allow_networking is None:
            return Response({"error": "allow_networking field is required"}, status=400)
        
        try:
            request.user.allow_networking = allow_networking
            request.user.save(update_fields=['allow_networking'])
            
            return Response({
                "message": "Networking settings updated successfully",
                "allow_networking": request.user.allow_networking
            }, status=200)
            
        except Exception as e:
            logger.error(f"Error updating networking settings: {e}")
            return Response({"error": "Failed to update networking settings"}, status=500)
