from django.urls import path

from .views import ClickWebhookView, PaymeWebhookView, create_payment_link


app_name = "payment"

urlpatterns = [
    path("create/", create_payment_link, name="create"),
    path("webhooks/payme/", PaymeWebhookView.as_view(), name="payme-webhook"),
    path("webhooks/click/", ClickWebhookView.as_view(), name="click-webhook"),
]
