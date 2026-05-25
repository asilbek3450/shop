from django.contrib import admin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "provider", "amount", "status", "created_at")
    list_filter = ("status", "provider", "created_at")
    search_fields = ("order__code", "user__phone")
    readonly_fields = ("created_at", "updated_at", "payment_url")
