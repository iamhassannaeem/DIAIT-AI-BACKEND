import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai_call_agent.models import UserBalance, TransactionLog, PaymentMethod

stripe.api_key = settings.STRIPE_SECRET_KEY
User = get_user_model()


class UserPaymentViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="create_stripe_customer")
    def create_stripe_customer(self, request, pk=None):
        permission_classes = [IsAuthenticated]
        user = request.user

        payment_method_data = request.data.get("payment_method")

        if not payment_method_data:
            return Response(
                {"error": "Payment method details are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            stripe_customer = stripe.Customer.create(
                email=user.email,
            )

            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": str(payment_method_data["card"]["number"]),
                    "exp_month": int(payment_method_data["card"]["exp_month"]),
                    "exp_year": int(payment_method_data["card"]["exp_year"]),
                    "cvc": str(payment_method_data["card"]["cvc"]),
                },
            )

            stripe.Customer.modify(
                stripe_customer["id"],
                invoice_settings={
                    "default_payment_method": payment_method.id,
                },
            )

            payment_method_instance = PaymentMethod.objects.create(
                user=user,
                stripe_payment_method_id=payment_method.id,
                card_brand=payment_method.card.brand,
                card_last4=payment_method.card.last4,
                card_exp_month=payment_method.card.exp_month,
                card_exp_year=payment_method.card.exp_year,
                is_verified=True,
            )

            return Response(
                {
                    "status": "Customer created and card attached",
                    "stripe_customer_id": stripe_customer["id"],
                    "card_brand": payment_method.card.brand,
                    "card_last4": payment_method.card.last4,
                    "card_exp_month": payment_method.card.exp_month,
                    "card_exp_year": payment_method.card.exp_year,
                },
                status=status.HTTP_200_OK,
            )

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except KeyError as e:

            return Response(
                {"error": f"Missing key in payment method data: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:

            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="add_funds")
    def add_funds(self, request):
        user = request.user
        amount = request.data.get("amount")
        payment_method_id = request.data.get("payment_method_id")

        if not amount or float(amount) <= 0:
            return Response(
                {"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:

            if not user.stripe_customer_id:
                return Response(
                    {"error": "Stripe customer ID not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            intent = stripe.PaymentIntent.create(
                amount=int(float(amount) * 100),
                currency="usd",
                customer=user.stripe_customer_id,
                payment_method=payment_method_id,
                off_session=True,
                confirm=True,
            )

            user_balance, created = UserBalance.objects.get_or_create(user=user)
            user_balance.add_balance(float(amount))

            TransactionLog.objects.create(
                user=user,
                amount=float(amount),
                description="Funds added via card",
            )

            return Response(
                {"status": "Funds added successfully", "balance": user_balance.balance},
                status=status.HTTP_200_OK,
            )

        except stripe.error.CardError as e:
            return Response(
                {"error": e.user_message}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
