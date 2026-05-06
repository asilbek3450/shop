from django.core.management.base import BaseCommand

from telegrambot.services.bot_runner import run_bot


class Command(BaseCommand):
    help = "Run aiogram 3 Telegram bot polling integrated with Django ORM."

    def handle(self, *args, **options):
        run_bot()
