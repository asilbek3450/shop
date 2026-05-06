from django.db import models

from catalog.models import Category


class TelegramProfile(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    user_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    language_code = models.CharField(max_length=20, blank=True)
    selected_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="telegram_profiles",
    )
    selected_subcategory = models.CharField(max_length=120, blank=True)
    cart = models.JSONField(default=list, blank=True)
    pending_order = models.JSONField(default=dict, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    is_blocked = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_seen_at"]

    def __str__(self):
        return self.username or f"TelegramUser {self.user_id}"
