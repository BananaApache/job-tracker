import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from fernet_fields import EncryptedTextField

# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # dont worry it automatically hashes
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    # @property
    # def is_social_user(self):
    #     return self.socialaccount_set.exists()


class Label(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class JobEmail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="emails")

    gmail_id = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=500)
    sender_email = models.EmailField()
    sender_name = models.CharField(max_length=255)
    received_at = models.DateTimeField()
    content_type = models.CharField(max_length=100)
    size_estimate = models.IntegerField()
    importance = models.IntegerField()

    labels = models.ManyToManyField(Label, related_name="emails")

    def __str__(self):
        return f"{self.subject} from {self.sender_email}"


class GoogleAuthToken(models.Model):
    user = models.OneToOneField("api.User", on_delete=models.CASCADE)
    token_json = EncryptedTextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GoogleAuthToken for {self.user.email}"
