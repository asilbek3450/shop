from django.db import transaction

from catalog.models import Product
from orders.models import Order, OrderItem


DELIVERY_COSTS = {
    Order.DELIVERY_STANDARD: 25000,
    Order.DELIVERY_EXPRESS: 50000,
    Order.DELIVERY_PICKUP: 0,
}

PROMO_CODES = {
    "NEXUS10": 10,
    "SPORT20": 20,
    "WELCOME15": 15,
}


def normalize_delivery(value):
    return value if value in DELIVERY_COSTS else Order.DELIVERY_STANDARD


def normalize_payment(value):
    return value if dict(Order.PAYMENT_CHOICES).get(value) else Order.PAYMENT_CARD


def apply_promo(subtotal, promo_code):
    code = (promo_code or "").strip().upper()
    percent = PROMO_CODES.get(code, 0)
    return code if percent else "", round(subtotal * percent / 100)


@transaction.atomic
def create_order(*, customer, items, delivery_method, payment_method, promo_code="", source=Order.SOURCE_WEB, telegram=None):
    """Create an order plus its line items.

    customer: dict with first_name, last_name, phone, city, address, note
    items: iterable of dicts {product_id (optional), name, brand, price, qty}
    """
    if not items:
        raise ValueError("Buyurtma bo'sh bo'lishi mumkin emas")

    delivery_method = normalize_delivery(delivery_method)
    payment_method = normalize_payment(payment_method)
    delivery_cost = DELIVERY_COSTS[delivery_method]

    subtotal = sum(int(item["price"]) * int(item.get("qty", 1) or 1) for item in items)
    applied_promo, discount = apply_promo(subtotal, promo_code)
    total = max(0, subtotal + delivery_cost - discount)

    order = Order.objects.create(
        source=source,
        customer_first_name=customer.get("first_name", "").strip()[:120] or "Mijoz",
        customer_last_name=customer.get("last_name", "").strip()[:120],
        customer_phone=customer.get("phone", "").strip()[:40],
        customer_city=customer.get("city", "").strip()[:120],
        customer_address=customer.get("address", "").strip()[:255],
        customer_note=customer.get("note", "").strip(),
        delivery_method=delivery_method,
        delivery_cost=delivery_cost,
        payment_method=payment_method,
        subtotal=subtotal,
        discount=discount,
        total=total,
        promo_code=applied_promo,
        telegram_user_id=(telegram or {}).get("user_id"),
        telegram_username=(telegram or {}).get("username", "")[:120],
    )

    line_items = []
    for item in items:
        qty = int(item.get("qty", 1) or 1)
        unit_price = int(item["price"])
        product = None
        product_id = item.get("product_id") or item.get("id")
        if product_id:
            product = Product.objects.filter(id=product_id).first()
        line_items.append(
            OrderItem(
                order=order,
                product=product,
                product_name=str(item.get("name", "Mahsulot"))[:200],
                product_brand=str(item.get("brand", ""))[:120],
                unit_price=unit_price,
                quantity=qty,
                line_total=unit_price * qty,
            )
        )
    OrderItem.objects.bulk_create(line_items)
    return order
