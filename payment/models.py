from django.conf import settings
from django.db import models
from django.utils import timezone

from orders.models import Order


class Invoice(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    PROVIDER_PAYME = "payme"
    PROVIDER_CLICK = "click"
    PROVIDER_CHOICES = [
        (PROVIDER_PAYME, "Payme"),
        (PROVIDER_CLICK, "Click"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="invoices")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_url = models.URLField(max_length=1000, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice {self.id} for Order {self.order_id}"
