from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from rest_framework.exceptions import ValidationError


class UserManager(BaseUserManager):
    def create_user(self, username, **extra_fields):
        if not username:
            raise ValidationError("Email must be set")
        user = self.model(username=username, **extra_fields)
        user.save(using=self._db)
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


class Regret(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='checklist_regrets')
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=False)
