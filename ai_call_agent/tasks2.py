import os
import sys

import django
from twilio.rest import Client

from config import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()
import time
from decimal import Decimal
from redis import StrictRedis
from django.db import transaction
from authentication.models import User
from ai_call_agent.models import CallLog, ProviderCost, Costtb
import django

django.setup()
from django.conf import settings
import redis

redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)


def get_provider_cost_details():
    providers = ProviderCost.objects.all()
    provider_details = {}
    for provider in providers:
        provider_details[provider.category] = {
            "sell_price": Decimal(provider.sell_price),
            "cost_price": Decimal(provider.cost_price),
            "provider": provider.provider,
        }
    return provider_details


def update_costs_in_redis(redis_client, call_key, provider_costs):
    try:
        for category, details in provider_costs.items():
            sell_cost_increment = Decimal(details["sell_price"] / 60 * 5)
            redis_client.hincrbyfloat(call_key, category, float(sell_cost_increment))
            cost_cost_increment = Decimal(details["cost_price"] / 60 * 5)
            redis_client.hincrbyfloat(
                call_key, f"{category}_cost", float(cost_cost_increment)
            )
    except Exception as e:
        print(f"Error updating costs in Redis for {call_key}: {e}")


def finalize_call_data(redis_client, user_balance_key, call_key, call_log_id, user_id):
    try:
        call_data = redis_client.hgetall(call_key)

        if call_data:
            call_log = CallLog.objects.get(id=call_log_id)
            user = User.objects.get(id=user_id)

            total_sell_cost = Decimal(0)

            with transaction.atomic():
                for category, sell_cost_str in call_data.items():
                    if "_cost" not in category:
                        provider_cost = ProviderCost.objects.filter(
                            category=category
                        ).first()
                        if provider_cost:
                            sell_cost = Decimal(sell_cost_str)
                            total_sell_cost += sell_cost
                            cost_price = Decimal(call_data.get(f"{category}_cost", "0"))
                            Costtb.objects.create(
                                call_log=call_log,
                                provider_id=provider_cost.id,
                                sell_cost=sell_cost,
                                cost=cost_price,
                            )

                balance = Decimal(redis_client.hget(user_balance_key, "balance") or "0")
                user.UserBalance = balance
                user.save()
                call_log.call_cost = total_sell_cost
                call_log.status = "completed"
                call_log.save()

            redis_client.delete(call_key)

            print(
                f"Finalized call data for call_log_id {call_log_id} and user_id {user_id}"
            )
        else:
            print(f"No data found in Redis for call key {call_key}")

    except Exception as e:
        print(f"Error finalizing call data for call_log_id {call_log_id}: {e}")


@shared_task
def monitor_call(user_id, call_sid, call_log_id):
    user_balance_key = f"user_balance:{user_id}"
    call_key = f"user_call:{user_id}:{call_sid}"
    redis_client = StrictRedis(host="localhost", port=6379, decode_responses=True)
    provider_costs = get_provider_cost_details()

    if not redis_client.exists(user_balance_key):
        user = User.objects.get(id=user_id)
        redis_client.hset(user_balance_key, "balance", str(user.UserBalance))

    if not redis_client.exists(call_key):
        for category in provider_costs.keys():
            redis_client.hset(call_key, category, "0")
            redis_client.hset(call_key, f"{category}_cost", "0")

    total_sell_cost_per_5_seconds = sum(
        Decimal(details["sell_price"] / 60 * 5) for details in provider_costs.values()
    )
    while True:
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            call = client.calls(call_sid).fetch()
            if call.status in ["ringing", "queued"]:
                continue
            if call.status in ["completed", "canceled", "failed", "no-answer"]:
                finalize_call_data(
                    redis_client, user_balance_key, call_key, call_log_id, user_id
                )
                break
            if call.status == "in-progress":
                balance = Decimal(redis_client.hget(user_balance_key, "balance") or "0")
                openai_sell_price = Decimal(
                    redis_client.hget(call_key, "openai_sell_price") or "0"
                )
                openai_cost_price = Decimal(
                    redis_client.hget(call_key, "openai_cost_price") or "0"
                )
                total_cost_with_openai = (
                    total_sell_cost_per_5_seconds + openai_sell_price
                )
                if balance < total_cost_with_openai:
                    call = client.calls(call_sid).update(status="completed")
                    finalize_call_data(
                        redis_client, user_balance_key, call_key, call_log_id, user_id
                    )
                    break

                new_balance = balance - total_cost_with_openai
                redis_client.hset(user_balance_key, "balance", str(new_balance))

                redis_client.hincrbyfloat(call_key, "openai", float(openai_sell_price))
                redis_client.hincrbyfloat(
                    call_key, "openai_cost", float(openai_cost_price)
                )
                redis_client.hset(call_key, "openai_sell_price", "0")
                redis_client.hset(call_key, "openai_cost_price", "0")

                update_costs_in_redis(redis_client, call_key, provider_costs)

                time.sleep(5)

        except Exception as e:
            print(f"Error while monitoring call {call_sid}: {e}")
            break
