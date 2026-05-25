import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from catalog.models import Product
from orders.models import Cart, CartItem, Order
from orders.services.checkout import create_order


logger = logging.getLogger(__name__)


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _serialize_cart(cart):
    items = []
    for item in cart.items.select_related("product").all():
        product = item.product
        items.append({
            "id": item.id,
            "product_id": product.id,
            "name": product.name,
            "brand": product.brand,
            "img": product.image_key,
            "price": product.price,
            "quantity": item.quantity,
            "line_total": item.line_total,
        })
    return {
        "items": items,
        "total_quantity": sum(i["quantity"] for i in items),
        "subtotal": sum(i["line_total"] for i in items),
    }


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

    if request.user.is_authenticated:
        order.user = request.user
        order.save(update_fields=["user"])
        Cart.objects.filter(user=request.user).first() and CartItem.objects.filter(
            cart__user=request.user
        ).delete()

    payment_url = None
    if order.payment_method in {Order.PAYMENT_PAYME, Order.PAYMENT_CLICK} and request.user.is_authenticated:
        from payment.services import create_invoice_with_link

        try:
            _, payment_url = create_invoice_with_link(
                order=order,
                user=request.user,
                provider=order.payment_method,
                return_url=f"{settings.SITE_URL.rstrip('/')}/orders/",
            )
        except Exception:
            logger.exception("Failed to create payment link for order %s", order.code)

    return JsonResponse(
        {
            "ok": True,
            "order": {
                "code": order.code,
                "total": order.total,
                "subtotal": order.subtotal,
                "delivery_cost": order.delivery_cost,
                "discount": order.discount,
                "payment_method": order.payment_method,
            },
            "payment_url": payment_url,
        }
    )


@login_required
@require_GET
def cart_view(request):
    return JsonResponse(_serialize_cart(_get_or_create_cart(request.user)))


@login_required
@require_POST
def cart_add(request):
    payload = json.loads(request.body or b"{}")
    product_id = payload.get("product_id")
    quantity = max(int(payload.get("quantity") or 1), 1)
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = _get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": quantity})
    if not created:
        item.quantity += quantity
        item.save(update_fields=["quantity"])
    return JsonResponse(_serialize_cart(cart))


@login_required
@require_POST
def cart_update(request):
    payload = json.loads(request.body or b"{}")
    item_id = payload.get("item_id")
    quantity = int(payload.get("quantity") or 0)
    cart = _get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save(update_fields=["quantity"])
    return JsonResponse(_serialize_cart(cart))


@login_required
@require_POST
def cart_clear(request):
    cart = _get_or_create_cart(request.user)
    cart.items.all().delete()
    return JsonResponse(_serialize_cart(cart))
