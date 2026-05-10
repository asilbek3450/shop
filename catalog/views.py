"""JSON endpoints for product interactions (like, wishlist, review, reply)."""
import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_GET

from .models import Product, ProductLike, Review, Wishlist


def _serialize_review(review, viewer=None):
    return {
        "id": review.id,
        "user_id": review.user_id,
        "user": review.user.full_name,
        "initials": review.user.initials,
        "rating": review.rating,
        "body": review.body,
        "is_reply": review.is_reply,
        "parent_id": review.parent_id,
        "created_at": review.created_at.isoformat(),
        "is_mine": viewer is not None and viewer.id == review.user_id,
    }


def _parse_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}


@require_GET
def review_list(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    qs = Review.objects.filter(product=product, is_hidden=False).select_related("user")
    top_level = [r for r in qs if r.parent_id is None]
    replies_by_parent = {}
    for review in qs:
        if review.parent_id:
            replies_by_parent.setdefault(review.parent_id, []).append(review)

    viewer = request.user if request.user.is_authenticated else None
    data = []
    for review in top_level:
        item = _serialize_review(review, viewer)
        item["replies"] = [_serialize_review(r, viewer) for r in replies_by_parent.get(review.id, [])]
        data.append(item)

    aggregates = qs.filter(parent__isnull=True).aggregate(avg=Avg("rating"), total=Count("id"))
    return JsonResponse({
        "reviews": data,
        "summary": {
            "average": round(aggregates["avg"] or 0, 1),
            "total": aggregates["total"] or 0,
        },
    })


@login_required
@require_POST
def review_create(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    payload = _parse_json(request)
    rating = payload.get("rating")
    body = (payload.get("body") or "").strip()
    parent_id = payload.get("parent_id")

    if not body:
        return JsonResponse({"error": "Sharh matni bo'sh bo'lmasin"}, status=400)
    if len(body) > 2000:
        return JsonResponse({"error": "Sharh juda uzun"}, status=400)

    if parent_id:
        parent = get_object_or_404(Review, pk=parent_id, product=product)
        if parent.parent_id is not None:
            parent = parent.parent or parent
        review = Review.objects.create(
            product=product,
            user=request.user,
            parent=parent,
            body=body,
        )
    else:
        try:
            rating_int = int(rating)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Reyting 1 dan 5 gacha bo'lishi kerak"}, status=400)
        if not 1 <= rating_int <= 5:
            return JsonResponse({"error": "Reyting 1 dan 5 gacha bo'lishi kerak"}, status=400)
        if Review.objects.filter(product=product, user=request.user, parent__isnull=True).exists():
            return JsonResponse({"error": "Siz bu mahsulotga sharh yozgansiz"}, status=400)
        review = Review.objects.create(
            product=product,
            user=request.user,
            rating=rating_int,
            body=body,
        )
    _refresh_product_rating(product)
    return JsonResponse({"review": _serialize_review(review, request.user)}, status=201)


@login_required
@require_POST
def review_delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if review.user_id != request.user.id and not request.user.is_staff:
        return JsonResponse({"error": "Ruxsat yo'q"}, status=403)
    product = review.product
    review.delete()
    _refresh_product_rating(product)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def like_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    like, created = ProductLike.objects.get_or_create(user=request.user, product=product)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({
        "liked": liked,
        "count": ProductLike.objects.filter(product=product).count(),
    })


@login_required
@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        return JsonResponse({"in_wishlist": False})
    return JsonResponse({"in_wishlist": True})


def _refresh_product_rating(product):
    aggregates = Review.objects.filter(
        product=product, parent__isnull=True, is_hidden=False
    ).aggregate(avg=Avg("rating"), total=Count("id"))
    product.rating = round(aggregates["avg"] or 0, 1) or 0
    product.reviews_count = aggregates["total"] or 0
    product.save(update_fields=["rating", "reviews_count"])
