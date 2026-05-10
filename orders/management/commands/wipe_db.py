"""One-shot helper to recover from an inconsistent migration history.

Usage (run ONCE on production after switching to a custom AUTH_USER_MODEL):

    python manage.py wipe_db --i-mean-it

It runs ``DROP SCHEMA public CASCADE; CREATE SCHEMA public;`` on the default
database, which is the cleanest way to reset Django's migration state without
touching the Postgres role/permissions or the database itself.

After running this, the next deploy/run of ``migrate`` will start from scratch.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Drop and recreate the public schema. Destroys ALL data. Production reset only."

    def add_arguments(self, parser):
        parser.add_argument(
            "--i-mean-it",
            action="store_true",
            help="Required confirmation flag — without it the command refuses to run.",
        )

    def handle(self, *args, **opts):
        if not opts["i_mean_it"]:
            raise CommandError(
                "Refusing to wipe the database without --i-mean-it. "
                "This deletes EVERY table in the public schema."
            )

        engine = connection.settings_dict.get("ENGINE", "")
        if "postgresql" not in engine:
            raise CommandError(
                f"Unsupported DB engine: {engine}. This command only supports PostgreSQL."
            )

        self.stdout.write(self.style.WARNING("Dropping public schema…"))
        with connection.cursor() as cur:
            cur.execute("DROP SCHEMA IF EXISTS public CASCADE;")
            cur.execute("CREATE SCHEMA public;")
            cur.execute("GRANT ALL ON SCHEMA public TO public;")

        self.stdout.write(self.style.SUCCESS(
            "✓ Schema reset. Now run: python manage.py migrate"
        ))
