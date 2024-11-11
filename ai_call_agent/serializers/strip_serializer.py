from rest_framework import serializers

from ai_call_agent.models import UserBalance, PaymentMethod, TransactionLog


class UserBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBalance
        fields = ["user", "balance"]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            "user",
            "stripe_payment_method_id",
            "stripe_customer_id",
            "card_brand",
            "card_last4",
            "card_exp_month",
            "card_exp_year",
            "is_verified",
        ]

    def create(self, validated_data):

        return PaymentMethod.objects.create(**validated_data)

    def update(self, instance, validated_data):

        instance.stripe_payment_method_id = validated_data.get(
            "stripe_payment_method_id", instance.stripe_payment_method_id
        )
        instance.stripe_customer_id = validated_data.get(
            "stripe_customer_id", instance.stripe_customer_id
        )
        instance.card_brand = validated_data.get("card_brand", instance.card_brand)
        instance.card_last4 = validated_data.get("card_last4", instance.card_last4)
        instance.card_exp_month = validated_data.get(
            "card_exp_month", instance.card_exp_month
        )
        instance.card_exp_year = validated_data.get(
            "card_exp_year", instance.card_exp_year
        )
        instance.is_verified = validated_data.get("is_verified", instance.is_verified)
        instance.save()
        return instance


class TransactionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionLog
        fields = ["user", "amount", "description", "timestamp"]
