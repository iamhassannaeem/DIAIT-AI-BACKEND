import stripe
from django.conf import settings


class Stripe:
    def __init__(self):
        stripe.api_key = settings.STRIPE_API_SECRET_KEY

    def get_event(self, payload):
        return stripe.Event.construct_from(payload, stripe.api_key)


class StripeCustomer(Stripe):
    def create_customer(self, user):
        customer = stripe.Customer.create(
            name=user.name,
            email=user.email,
            description="Created by SwiftSync User Application.",
        )
        user.stripe_id = customer["id"]
        user.stripe = customer
        user.save()

    def attach_payment_method(self, customer_id, payment_id):
        return stripe.PaymentMethod.attach(payment_id, customer=customer_id)

    def default_payment_method(self, customer_id, payment_id):
        stripe.Customer.modify(
            customer_id,
            invoice_settings={
                'default_payment_method': payment_id,
            },
        )


class StripePaymentIntent(Stripe):
    def create_payment_intent(self, amount):
        payment_intent = stripe.PaymentIntent.create(
            setup_future_usage="off_session",
            amount=amount * 100,
            currency="usd",
            payment_method_types=["card"],
        )
        return payment_intent

    def get_payment_intent(self, stripe_id):
        return stripe.PaymentIntent.retrieve(stripe_id)


class StripeSubscription(Stripe):
    def create_subscription(self, user, price):
        subscription = stripe.Subscription.create(
            customer=user.stripe_id, items=[{"price": price}]
        )
        return subscription


class StripeInvoice(Stripe):
    def create_invoice(self, user):
        invoice = stripe.Invoice.create(
            customer=user.stripe_id,
        )
        return invoice
