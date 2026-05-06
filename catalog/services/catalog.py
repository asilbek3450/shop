import json

from django.db.models import Count

from catalog.models import Category, Product


def serialize_product(product):
    return {
        "id": product.id,
        "slug": product.slug,
        "name": product.name,
        "brand": product.brand,
        "category": product.category.name,
        "category_slug": product.category.slug,
        "subcategory": product.subcategory,
        "price": product.price,
        "oldPrice": product.old_price,
        "rating": float(product.rating),
        "reviews": product.reviews_count,
        "stock": product.stock,
        "badge": product.badge or None,
        "colors": product.colors or [],
        "sizes": product.sizes or [],
        "img": product.image_key,
        "desc": product.description,
        "short_desc": product.short_description,
        "features": product.features or [],
    }


def serialize_category(category):
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "emoji": category.emoji,
        "description": category.description,
        "product_count": getattr(category, "product_count", 0),
    }


def get_catalog_queryset():
    return Product.objects.select_related("category").filter(is_active=True, category__is_active=True)


def get_categories_queryset():
    return Category.objects.filter(is_active=True).annotate(product_count=Count("products")).order_by("sort_order", "name")


def build_catalog_payload():
    products = list(get_catalog_queryset())
    categories = list(get_categories_queryset())
    return {
        "categories": [serialize_category(category) for category in categories],
        "products": [serialize_product(product) for product in products],
    }


def build_storefront_context():
    payload = build_catalog_payload()
    products = payload["products"]
    return {
        "catalog_payload_json": json.dumps(payload, ensure_ascii=False),
        "catalog_products": products,
        "catalog_categories": payload["categories"],
        "featured_products": [product for product in products if product.get("badge") or product["reviews"]][:4],
    }


def get_product_from_request(request):
    return get_product_by_identifier(
        product_id=request.GET.get("id"),
        slug=request.GET.get("slug"),
    )


def get_product_by_identifier(product_id=None, slug=None):
    queryset = get_catalog_queryset()
    if product_id and str(product_id).isdigit():
        return queryset.filter(id=product_id).first()
    if slug:
        return queryset.filter(slug=slug).first()
    return queryset.first()
