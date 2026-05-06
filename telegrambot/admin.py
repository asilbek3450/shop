from django.contrib import admin

from .models import TelegramProfile


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("user_id", "username", "first_name", "selected_category", "is_blocked", "last_seen_at")
    list_filter = ("is_blocked", "selected_category")
    search_fields = ("username", "first_name", "last_name", "user_id", "chat_id")
