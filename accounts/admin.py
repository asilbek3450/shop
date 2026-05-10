from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import PhoneVerification, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("phone", "first_name", "last_name", "is_phone_verified", "is_staff", "date_joined")
    list_filter = ("is_phone_verified", "is_staff", "is_superuser", "is_active")
    search_fields = ("phone", "first_name", "last_name", "telegram_username")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "email")}),
        ("Telegram", {"fields": ("telegram_user_id", "telegram_username", "is_phone_verified")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "first_name", "password1", "password2"),
        }),
    )


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ("phone", "purpose", "code", "contact_shared_at", "used_at", "expires_at")
    list_filter = ("purpose",)
    search_fields = ("phone", "link_token", "bot_username")
    readonly_fields = ("link_token", "created_at", "code_sent_at", "contact_shared_at", "used_at")
