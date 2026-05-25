import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from paytechuz.integrations.django.views import (
    BaseClickWebhookView,
    BasePaymeWebhookView,
)

from orders.models import Order

from .models import Invoice
from .services import create_invoice_with_link


logger = logging.getLogger(__name__)


def _mark_paid(transaction):
    invoice = Invoice.objects.select_related("order").get(id=transaction.account_id)
    invoice.status = Invoice.STATUS_PAID
    invoice.save(update_fields=["status", "updated_at"])
    order = invoice.order
    if order.status == Order.STATUS_NEW:
        order.status = Order.STATUS_CONFIRMED
        order.save(update_fields=["status", "updated_at"])


def _mark_cancelled(transaction):
    invoice = Invoice.objects.get(id=transaction.account_id)
    invoice.status = Invoice.STATUS_CANCELLED
    invoice.save(update_fields=["status", "updated_at"])


class PaymeWebhookView(BasePaymeWebhookView):
    def successfully_payment(self, params, transaction):
        _mark_paid(transaction)

    def cancelled_payment(self, params, transaction):
        _mark_cancelled(transaction)


class ClickWebhookView(BaseClickWebhookView):
    def successfully_payment(self, params, transaction):
        _mark_paid(transaction)

    def cancelled_payment(self, params, transaction):
        _mark_cancelled(transaction)


@login_required
@require_POST
def create_payment_link(request):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Noto'g'ri JSON"}, status=400)

    order_code = payload.get("order_code")
    provider = (payload.get("provider") or "").lower()

    if provider not in {Invoice.PROVIDER_PAYME, Invoice.PROVIDER_CLICK}:
        return JsonResponse(
            {"ok": False, "error": "provider 'payme' yoki 'click' bo'lishi kerak"},
            status=400,
        )

    order = get_object_or_404(Order, code=order_code, user=request.user)
    return_url = payload.get("return_url") or f"{settings.SITE_URL.rstrip('/')}/orders/"

    try:
        invoice, payment_url = create_invoice_with_link(
            order=order,
            user=request.user,
            provider=provider,
            return_url=return_url,
        )
    except Exception as exc:
        logger.exception("Failed to create %s payment link", provider)
        return JsonResponse({"ok": False, "error": str(exc)}, status=500)

    return JsonResponse(
        {
            "ok": True,
            "invoice_id": invoice.id,
            "order_code": order.code,
            "provider": provider,
            "amount": str(invoice.amount),
            "payment_url": payment_url,
        }
    )
