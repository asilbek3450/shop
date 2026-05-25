from django.conf import settings

from paytechuz.gateways.click import ClickGateway
from paytechuz.gateways.payme import PaymeGateway

from .models import Invoice


def create_invoice_with_link(*, order, user, provider, return_url):
    """Create an Invoice for the given order and return (invoice, payment_url)."""
    if provider not in {Invoice.PROVIDER_PAYME, Invoice.PROVIDER_CLICK}:
        raise ValueError("provider must be 'payme' or 'click'")

    invoice = Invoice.objects.create(
        user=user if (user and user.is_authenticated) else None,
        order=order,
        provider=provider,
        amount=order.total,
        status=Invoice.STATUS_PENDING,
    )

    if provider == Invoice.PROVIDER_PAYME:
        cfg = settings.PAYTECHUZ["PAYME"]
        gateway = PaymeGateway(
            payme_id=cfg["PAYME_ID"],
            payme_key=cfg["PAYME_KEY"],
            is_test_mode=cfg["IS_TEST_MODE"],
        )
        payment_url = gateway.create_payment(
            id=invoice.id,
            amount=invoice.amount,
            return_url=return_url,
            account_field_name=cfg["ACCOUNT_FIELD"],
        )
    else:
        cfg = settings.PAYTECHUZ["CLICK"]
        gateway = ClickGateway(
            service_id=cfg["SERVICE_ID"],
            merchant_id=cfg["MERCHANT_ID"],
            merchant_user_id=cfg["MERCHANT_USER_ID"],
            secret_key=cfg["SECRET_KEY"],
            is_test_mode=cfg["IS_TEST_MODE"],
        )
        payment_url = gateway.create_payment(
            id=invoice.id,
            amount=invoice.amount,
            return_url=return_url,
        )

    invoice.payment_url = payment_url
    invoice.save(update_fields=["payment_url", "updated_at"])
    return invoice, payment_url
