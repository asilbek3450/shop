from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("shop/", views.shop, name="shop"),
    path("product/", views.product, name="product"),
    path("products/<slug:slug>/", views.product, name="product-detail"),
    path("checkout/", views.checkout, name="checkout"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("profile/", views.profile, name="profile"),
    path("confirmation/", views.confirmation, name="confirmation"),
]
