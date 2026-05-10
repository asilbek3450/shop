import secrets
import string

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


def generate_password(length=14):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
        ):
            return password


class Command(BaseCommand):
    help = "Create or reset a superuser identified by phone."

    def add_arguments(self, parser):
        parser.add_argument("--phone", default="+998900000000", help="Superuser phone number.")
        parser.add_argument("--first-name", default="Admin")
        parser.add_argument("--last-name", default="")
        parser.add_argument("--password", default=None, help="Set explicit password (otherwise random).")
        parser.add_argument("--reset", action="store_true", help="Reset password if user already exists.")

    def handle(self, *args, **opts):
        User = get_user_model()
        phone = opts["phone"]
        password = opts["password"] or generate_password()

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                "first_name": opts["first_name"],
                "last_name": opts["last_name"],
                "is_staff": True,
                "is_superuser": True,
                "is_phone_verified": True,
            },
        )

        if created or opts["reset"]:
            user.is_staff = True
            user.is_superuser = True
            user.is_phone_verified = True
            if not user.first_name:
                user.first_name = opts["first_name"]
            user.set_password(password)
            user.save()
            action = "yaratildi" if created else "yangilandi"
            self.stdout.write(self.style.SUCCESS(f"Superuser '{phone}' {action}."))
            self.stdout.write(self.style.WARNING(f"Login: {phone}"))
            self.stdout.write(self.style.WARNING(f"Parol: {password}"))
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"Superuser '{phone}' allaqachon mavjud. Parolni yangilash uchun --reset bayrog'ini ishlating."
                )
            )
