from django.conf import settings
from django.shortcuts import render

from catalog.services.catalog import build_storefront_context, get_product_by_identifier


def render_page(request, template_name, title, page_key, extra_context=None):
    context = {
        "title": title,
        "page_key": page_key,
        "site_url": settings.SITE_URL,
        **build_storefront_context(),
    }
    if extra_context:
        context.update(extra_context)
    return render(
        request,
        template_name,
        context,
    )


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


def checkout(request):
    return render_page(request, "store/checkout.html", "Xarid — uzshop", "checkout")


def wishlist(request):
    return render_page(request, "store/wishlist.html", "Istaklar — uzshop", "wishlist")


def profile(request):
    return render_page(request, "store/profile.html", "Profil — uzshop", "profile")


def confirmation(request):
    return render_page(request, "store/confirmation.html", "Buyurtma tasdiqlandi — uzshop", "confirmation")

# Create your views here.
