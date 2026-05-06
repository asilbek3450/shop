from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "product_brand", "unit_price", "quantity", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "customer_first_name",
        "customer_phone",
        "source_badge",
        "status_badge",
        "total_display",
        "created_at",
    )
    list_filter = ("status", "source", "delivery_method", "payment_method", "created_at")
    search_fields = (
        "code",
        "customer_first_name",
        "customer_last_name",
        "customer_phone",
        "customer_address",
        "telegram_username",
    )
    readonly_fields = (
        "code",
        "source",
        "subtotal",
        "discount",
        "total",
        "delivery_cost",
        "telegram_user_id",
        "telegram_username",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    list_per_page = 30
    fieldsets = (
        ("Buyurtma", {"fields": ("code", "source", "status", "created_at", "updated_at")}),
        (
            "Mijoz",
            {
                "fields": (
                    "customer_first_name",
                    "customer_last_name",
                    "customer_phone",
                    "customer_city",
                    "customer_address",
                    "customer_note",
                    "telegram_user_id",
                    "telegram_username",
                )
            },
        ),
        (
            "Yetkazib berish va to'lov",
            {"fields": ("delivery_method", "delivery_cost", "payment_method", "promo_code")},
        ),
        ("Hisob", {"fields": ("subtotal", "discount", "total")}),
    )

    def source_badge(self, obj):
        color = "#6366f1" if obj.source == Order.SOURCE_BOT else "#0ea5e9"
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px">{}</span>',
            color,
            obj.get_source_display(),
        )

    source_badge.short_description = "Manba"

    def status_badge(self, obj):
        colors = {
            Order.STATUS_NEW: "#f59e0b",
            Order.STATUS_CONFIRMED: "#10b981",
            Order.STATUS_SHIPPED: "#3b82f6",
            Order.STATUS_DELIVERED: "#22c55e",
            Order.STATUS_CANCELLED: "#ef4444",
        }
        color = colors.get(obj.status, "#64748b")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Holat"

    def total_display(self, obj):
        return f"{obj.total:,} so'm".replace(",", " ")

    total_display.short_description = "Jami"
    total_display.admin_order_field = "total"
