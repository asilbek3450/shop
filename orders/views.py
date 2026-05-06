import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from orders.models import Order
from orders.services.checkout import create_order


@require_POST
def submit_order(request):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Noto'g'ri JSON"}, status=400)

    customer = payload.get("customer") or {}
    items = payload.get("items") or []

    if not customer.get("first_name") or not customer.get("phone"):
        return JsonResponse({"ok": False, "error": "Ism va telefon raqamini kiriting"}, status=400)
    if not items:
        return JsonResponse({"ok": False, "error": "Savat bo'sh"}, status=400)

    try:
        order = create_order(
            customer=customer,
            items=items,
            delivery_method=payload.get("delivery_method", Order.DELIVERY_STANDARD),
            payment_method=payload.get("payment_method", Order.PAYMENT_CARD),
            promo_code=payload.get("promo_code", ""),
            source=Order.SOURCE_WEB,
        )
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "order": {
                "code": order.code,
                "total": order.total,
                "subtotal": order.subtotal,
                "delivery_cost": order.delivery_cost,
                "discount": order.discount,
            },
        }
    )
