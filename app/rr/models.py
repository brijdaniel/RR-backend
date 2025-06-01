from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear
from django.core.exceptions import ValidationError
from datetime import datetime, time


class UserManager(BaseUserManager):
    def create_user(self, username, **extra_fields):
        if not username:
            raise ValidationError("Email must be set")
        user = self.model(username=username, **extra_fields)
        user.save(using=self._db)

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

    objects = UserManager()

    USERNAME_FIELD = 'username'

    def __str__(self):
        return str(self.username)


class Checklist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_checklists')
    created_at = models.DateTimeField(default=timezone.now)
    score = models.DecimalField(decimal_places=4, max_digits=5, default=0, validators=[MinValueValidator(limit_value=0), MaxValueValidator(limit_value=1)])
    completed = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at'])
        ]

    def save(self, *args, **kwargs):
        # Get the date part of created_at
        check_date = self.created_at.date()
        
        # Check if there's already a checklist for this user on this date
        if not self.pk:  # Only check on creation
            existing = Checklist.objects.filter(
                user=self.user,
                created_at__date=check_date
            ).exists()
            
            if existing:
                raise ValidationError('A checklist for this user already exists for this date.')
        
        super().save(*args, **kwargs)


class Regret(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='checklist_regrets')
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=False)
