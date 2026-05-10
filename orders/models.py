import secrets
import string

from django.conf import settings
from django.db import models

from catalog.models import Product


def generate_order_code():
    alphabet = string.ascii_uppercase + string.digits
    return "ORD-" + "".join(secrets.choice(alphabet) for _ in range(8))


class Order(models.Model):
    SOURCE_WEB = "web"
    SOURCE_BOT = "bot"
    SOURCE_CHOICES = [
        (SOURCE_WEB, "Sayt"),
        (SOURCE_BOT, "Telegram bot"),
    ]

    STATUS_NEW = "new"
    STATUS_CONFIRMED = "confirmed"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_NEW, "Yangi"),
        (STATUS_CONFIRMED, "Tasdiqlangan"),
        (STATUS_SHIPPED, "Yo'lda"),
        (STATUS_DELIVERED, "Yetkazildi"),
        (STATUS_CANCELLED, "Bekor qilindi"),
    ]

    DELIVERY_STANDARD = "standard"
    DELIVERY_EXPRESS = "express"
    DELIVERY_PICKUP = "pickup"
    DELIVERY_CHOICES = [
        (DELIVERY_STANDARD, "Standart"),
        (DELIVERY_EXPRESS, "Tezkor"),
        (DELIVERY_PICKUP, "Do'kondan olib ketish"),
    ]

    PAYMENT_CARD = "card"
    PAYMENT_CLICK = "click"
    PAYMENT_CASH = "cash"
    PAYMENT_CHOICES = [
        (PAYMENT_CARD, "Karta"),
        (PAYMENT_CLICK, "Click/Payme"),
        (PAYMENT_CASH, "Naqd"),
    ]

    code = models.CharField(max_length=20, unique=True, default=generate_order_code)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_WEB)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    customer_first_name = models.CharField(max_length=120)
    customer_last_name = models.CharField(max_length=120, blank=True)
    customer_phone = models.CharField(max_length=40)
    customer_city = models.CharField(max_length=120, blank=True)
    customer_address = models.CharField(max_length=255, blank=True)
    customer_note = models.TextField(blank=True)

    telegram_user_id = models.BigIntegerField(null=True, blank=True)
    telegram_username = models.CharField(max_length=120, blank=True)

    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default=DELIVERY_STANDARD)
    delivery_cost = models.PositiveIntegerField(default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_CARD)

    subtotal = models.PositiveIntegerField(default=0)
    discount = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    promo_code = models.CharField(max_length=40, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} — {self.customer_first_name} ({self.total:,} so'm)".replace(",", " ")

    @property
    def customer_full_name(self):
        return " ".join(part for part in [self.customer_first_name, self.customer_last_name] if part).strip()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")
    product_name = models.CharField(max_length=200)
    product_brand = models.CharField(max_length=120, blank=True)
    unit_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.PositiveIntegerField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user_id}"

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.product_id} × {self.quantity}"

    @property
    def line_total(self):
        return self.product.price * self.quantity
