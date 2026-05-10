"""High-level helpers shared by web views and the Telegram bot."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import PhoneVerification

VERIFICATION_TTL_MIN = 15
MAX_VERIFY_ATTEMPTS = 5

User = get_user_model()


def start_registration(*, phone, first_name, last_name, password_hash):
    """Create a fresh PhoneVerification (invalidating any prior pending ones)."""
    PhoneVerification.objects.filter(
        phone=phone,
        purpose=PhoneVerification.PURPOSE_REGISTER,
        used_at__isnull=True,
    ).update(used_at=timezone.now())

    verification = PhoneVerification.objects.create(
        phone=phone,
        purpose=PhoneVerification.PURPOSE_REGISTER,
        first_name=first_name,
        last_name=last_name or "",
        password_hash=password_hash,
        expires_at=timezone.now() + timedelta(minutes=VERIFICATION_TTL_MIN),
    )
    return verification


def find_active_verification(token):
    return (
        PhoneVerification.objects.filter(
            link_token=token,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )


def find_active_for_phone(phone):
    return (
        PhoneVerification.objects.filter(
            phone=phone,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )


@transaction.atomic
def attach_telegram_to_verification(verification, *, chat_id, user_id, username, phone_match):
    """Called from the bot once the user shares their contact."""
    verification.bot_chat_id = chat_id
    verification.bot_user_id = user_id
    verification.bot_username = username or ""
    update_fields = ["bot_chat_id", "bot_user_id", "bot_username"]

    if phone_match:
        verification.contact_shared_at = timezone.now()
        verification.issue_code()
        update_fields += ["contact_shared_at", "code", "code_sent_at"]

    verification.save(update_fields=update_fields)
    return verification


@transaction.atomic
def complete_registration(verification, code):
    """Finalize registration: create the user, mark verification used."""
    if verification.is_expired():
        return None, "Tasdiqlash muddati tugagan. Iltimos qayta ro'yxatdan o'ting."
    if verification.is_used():
        return None, "Bu kod allaqachon ishlatilgan."
    if verification.attempts >= MAX_VERIFY_ATTEMPTS:
        return None, "Urinishlar soni oshib ketdi. Qayta ro'yxatdan o'ting."
    if not verification.is_ready_to_verify():
        return None, "Avval botga /start bosing va telefon raqamingizni baham ko'ring."

    if code != verification.code:
        verification.attempts += 1
        verification.save(update_fields=["attempts"])
        return None, "Kod noto'g'ri. Qaytadan urinib ko'ring."

    if User.objects.filter(phone=verification.phone).exists():
        verification.mark_used()
        return None, "Bu raqam allaqachon ro'yxatdan o'tgan. Kiring."

    user = User(
        phone=verification.phone,
        first_name=verification.first_name,
        last_name=verification.last_name,
        is_phone_verified=True,
        telegram_user_id=verification.bot_user_id,
        telegram_username=verification.bot_username,
    )
    user.password = verification.password_hash  # already hashed
    user.save()
    verification.mark_used()
    return user, None
