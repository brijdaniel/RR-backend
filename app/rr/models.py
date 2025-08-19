from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear
from django.core.exceptions import ValidationError
from datetime import datetime, time
import logging

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    def create_user(self, username, **extra_fields):
        if not username:
            raise ValidationError("Email must be set")
        
        logger.info(f"Creating user with username: {username}")
        logger.info(f"Extra fields before setdefault: {extra_fields}")
        
        extra_fields.setdefault('is_active', True)
        logger.info(f"Extra fields after setdefault: {extra_fields}")
        
        user = self.model(username=username, **extra_fields)
        logger.info(f"User object created, is_active = {user.is_active}")
        
        user.save(using=self._db)
        logger.info(f"User saved to database, is_active = {user.is_active}")

        # Set the password if provided in extra_fields - required for superuser
        password = extra_fields.pop('password', None)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        return user

    def create_superuser(self, username, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    allow_networking = models.BooleanField(default=True, help_text="Allow other users to follow this user")
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)

    objects = UserManager()

    USERNAME_FIELD = 'username'

    def __str__(self):
        return str(self.username)
    
    def get_regret_index(self, date=None):
        """Calculate user's regret index for a specific date"""
        if date is None:
            date = timezone.now().date()
        
        try:
            checklist = self.user_checklists.filter(
                created_at__date=date
            ).first()
            
            if checklist:
                return float(checklist.score)
            return -1  # No checklist available for this date
        except Exception as e:
            logger.error(f"Error calculating regret index for user {self.id}: {e}")
            return -1  # Error case also returns -1
    
    def refresh_counts(self):
        """Refresh follower and following counts from actual relationships"""
        try:
            self.followers_count = self.followers.count()
            self.following_count = self.following.count()
            self.save(update_fields=['followers_count', 'following_count'])
        except Exception as e:
            logger.error(f"Error refreshing counts for user {self.id}: {e}")
    
    def save(self, *args, **kwargs):
        """Override save to ensure counts are valid"""
        # Ensure counts are never negative
        if self.followers_count < 0:
            self.followers_count = 0
        if self.following_count < 0:
            self.following_count = 0
        
        super().save(*args, **kwargs)


class Checklist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_checklists')
    created_at = models.DateTimeField(default=timezone.now)
    score = models.DecimalField(decimal_places=4, max_digits=5, default=1.0, validators=[MinValueValidator(limit_value=0), MaxValueValidator(limit_value=1)])
    completed = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at'])
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Regret(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='checklist_regrets')
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=False)


class Network(models.Model):
    """Network relationship between users (following/followers)"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
    def save(self, *args, **kwargs):
        """Override save to update user counts"""
        # Prevent self-following
        if self.follower == self.following:
            raise ValidationError("Users cannot follow themselves")
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update follower and following counts using F() expressions to avoid race conditions
            from django.db.models import F
            User.objects.filter(id=self.following.id).update(
                followers_count=F('followers_count') + 1
            )
            User.objects.filter(id=self.follower.id).update(
                following_count=F('following_count') + 1
            )
    
    def delete(self, *args, **kwargs):
        """Override delete to update user counts"""
        # Store references before deletion
        following_id = self.following.id
        follower_id = self.follower.id
        
        super().delete(*args, **kwargs)
        
        # Update follower and following counts using F() expressions with safety checks
        from django.db.models import F
        User.objects.filter(id=following_id).update(
            followers_count=F('followers_count') - 1
        )
        User.objects.filter(id=follower_id).update(
            following_count=F('following_count') - 1
        )
        
        # Ensure counts never go below 0
        User.objects.filter(id=following_id, followers_count__lt=0).update(followers_count=0)
        User.objects.filter(id=follower_id, following_count__lt=0).update(following_count=0)
