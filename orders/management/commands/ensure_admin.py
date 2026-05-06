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
    help = "Create or reset the default 'admin' superuser with a freshly generated password."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--email", default="admin@nexus.local")
        parser.add_argument("--password", default=None, help="Set explicit password (otherwise random).")
        parser.add_argument("--reset", action="store_true", help="Reset password if user already exists.")

    def handle(self, *args, **opts):
        User = get_user_model()
        username = opts["username"]
        password = opts["password"] or generate_password()

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": opts["email"], "is_staff": True, "is_superuser": True},
        )

        if created or opts["reset"]:
            user.is_staff = True
            user.is_superuser = True
            user.email = opts["email"]
            user.set_password(password)
            user.save()
            action = "yaratildi" if created else "yangilandi"
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' {action}."))
            self.stdout.write(self.style.WARNING(f"Login: {username}"))
            self.stdout.write(self.style.WARNING(f"Parol: {password}"))
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"Superuser '{username}' allaqachon mavjud. Parolni yangilash uchun --reset bayrog'ini ishlating."
                )
            )
