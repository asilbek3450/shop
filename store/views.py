import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from catalog.models import Wishlist
from catalog.services.catalog import build_storefront_context, get_product_by_identifier
from orders.models import Order


def render_page(request, template_name, title, page_key, extra_context=None):
    context = {
        "title": title,
        "page_key": page_key,
        "site_url": settings.SITE_URL,
        **build_storefront_context(),
    }
    if request.user.is_authenticated:
        context["current_user"] = {
            "full_name": request.user.full_name,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "phone": request.user.phone,
            "initials": request.user.initials,
        }
    if extra_context:
        context.update(extra_context)
    return render(request, template_name, context)


def index(request):
    return render_page(request, "store/index.html", "uzshop — Global Online Store", "index")


def shop(request):
    return render_page(request, "store/shop.html", "Do'kon — uzshop", "shop")


def product(request, slug=None):
    current_product = get_product_by_identifier(
        product_id=request.GET.get("id"),
        slug=slug or request.GET.get("slug"),
    )
    title = f"{current_product.name} — uzshop" if current_product else "Mahsulot — uzshop"
    return render_page(
        request,
        "store/product.html",
        title,
        "product",
        {"current_product": current_product, "current_product_id": current_product.id if current_product else None},
    )


@login_required
def checkout(request):
    return render_page(request, "store/checkout.html", "Xarid — uzshop", "checkout")


@login_required
def wishlist(request):
    return render_page(request, "store/wishlist.html", "Istaklar — uzshop", "wishlist")


@login_required
def profile(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items")
        .order_by("-created_at")[:50]
    )
    orders_payload = [
        {
            "code": o.code,
            "status": o.status,
            "status_label": o.get_status_display(),
            "total": o.total,
            "created_at": o.created_at.isoformat(),
            "delivery": o.get_delivery_method_display(),
            "items": [
                {"name": it.product_name, "qty": it.quantity, "img": (it.product.image_key if it.product_id else "")}
                for it in o.items.all()
            ],
        }
        for o in orders
    ]
    wishlist_ids = list(
        Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
    )
    return render_page(
        request,
        "store/profile.html",
        "Profil — uzshop",
        "profile",
        {
            "orders_json": json.dumps(orders_payload, ensure_ascii=False),
            "wishlist_ids_json": json.dumps(wishlist_ids),
        },
    )


@login_required
def confirmation(request):
    return render_page(request, "store/confirmation.html", "Buyurtma tasdiqlandi — uzshop", "confirmation")
