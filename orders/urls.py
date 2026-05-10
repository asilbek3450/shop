from django.urls import path

from . import views


urlpatterns = [
    path("submit/", views.submit_order, name="orders-submit"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/", views.cart_add, name="cart-add"),
    path("cart/update/", views.cart_update, name="cart-update"),
    path("cart/clear/", views.cart_clear, name="cart-clear"),
]
