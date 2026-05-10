from django.urls import path

from . import views


app_name = "catalog"


urlpatterns = [
    path("products/<int:product_id>/reviews/", views.review_list, name="review-list"),
    path("products/<int:product_id>/reviews/create/", views.review_create, name="review-create"),
    path("reviews/<int:review_id>/delete/", views.review_delete, name="review-delete"),
    path("products/<int:product_id>/like/", views.like_toggle, name="like-toggle"),
    path("products/<int:product_id>/wishlist/", views.wishlist_toggle, name="wishlist-toggle"),
]
