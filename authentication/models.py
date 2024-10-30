from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(email=self.normalize_email(email), name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        user = self.create_user(
            email=email,
            name=name,
            password=password,
        )
        user.is_admin = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    profile_image = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    name = models.CharField(max_length=64)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_expires_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def set_verification_code(self):
        self.verification_code = str(random.randint(100000, 999999))
        self.verification_code_expires_at = timezone.now() + timedelta(minutes=1)
        self.save()


class ErrorLog(models.Model):
    ERROR_TYPE_CHOICES = [
        ('AUTH', 'Authentication Error'),
        ('DB', 'Database Error'),
        ('SRV', 'Server Error'),
        ('API', 'API Error'),
        ('OTH', 'Other'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    error_type = models.CharField(max_length=100, choices=ERROR_TYPE_CHOICES, default='OTH')
    error_message = models.TextField()
    traceback = models.TextField()
    user_agent = models.TextField(blank=True, null=True)
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_error_type_display()} - {self.timestamp}"
