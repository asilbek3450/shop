from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from .utils import generate_link_token, generate_otp_code, normalize_phone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone, password, **extra):
        if not phone:
            raise ValueError("Telefon raqam talab qilinadi")
        normalized = normalize_phone(phone)
        if not normalized:
            raise ValueError("Telefon raqam noto'g'ri")
        user = self.model(phone=normalized, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra)

    def create_superuser(self, phone, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_phone_verified", True)
        if extra.get("is_staff") is not True:
            raise ValueError("Superuser is_staff=True bo'lishi shart")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser is_superuser=True bo'lishi shart")
        return self._create_user(phone, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)

    is_phone_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    telegram_user_id = models.BigIntegerField(null=True, blank=True, unique=True)
    telegram_username = models.CharField(max_length=120, blank=True)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name"]

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.full_name} ({self.phone})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.phone

    @property
    def initials(self):
        first = self.first_name[:1].upper() if self.first_name else ""
        last = self.last_name[:1].upper() if self.last_name else ""
        return (first + last) or "U"

    def get_short_name(self):
        return self.first_name or self.phone

    def get_full_name(self):
        return self.full_name


class PhoneVerification(models.Model):
    """Pending phone+TG verification tied to a registration attempt.

    Flow:
      1. Web register form creates one with phone, first_name, last_name and a hashed password
         (stored on a temporary field) and a deep-link token.
      2. User opens t.me/<bot>?start=<token>, bot asks for contact share, validates phone,
         generates a 6-digit code and DM-s it.
      3. Web verify form accepts code → User is created and logged in.
    """

    PURPOSE_REGISTER = "register"
    PURPOSE_LOGIN = "login"
    PURPOSE_CHOICES = [
        (PURPOSE_REGISTER, "Ro'yxatdan o'tish"),
        (PURPOSE_LOGIN, "Kirish"),
    ]

    phone = models.CharField(max_length=20, db_index=True)
    purpose = models.CharField(max_length=16, choices=PURPOSE_CHOICES, default=PURPOSE_REGISTER)

    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    password_hash = models.CharField(max_length=256, blank=True)

    link_token = models.CharField(max_length=64, unique=True, default=generate_link_token)
    code = models.CharField(max_length=6, blank=True)

    bot_chat_id = models.BigIntegerField(null=True, blank=True)
    bot_user_id = models.BigIntegerField(null=True, blank=True)
    bot_username = models.CharField(max_length=120, blank=True)

    contact_shared_at = models.DateTimeField(null=True, blank=True)
    code_sent_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.phone} → {self.code or '...'} ({self.purpose})"

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def is_used(self):
        return self.used_at is not None

    def is_ready_to_verify(self):
        """Bot has sent the code and we still have it on file."""
        return bool(self.code) and self.contact_shared_at is not None

    def issue_code(self):
        self.code = generate_otp_code()
        self.code_sent_at = timezone.now()
        return self.code

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
