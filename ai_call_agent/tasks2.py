import os
import sys

import django
from twilio.rest import Client

from ai_call_agent.query import (
    get_provider_cost_details,
    update_user,
    update_call_log,
    get_user_details,
    insert_new_costtb,
    logger,
)
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


def finalize_call_data(
    redis_client,
    user_balance_key,
    call_key,
    call_log_id,
    user_id,
    call_endtime,
    call_duration,
    call_status,
):

    try:
        call_data = redis_client.hgetall(call_key)

        if call_data:
            total_sell_cost = Decimal(0)

            with transaction.atomic():
                try:
                    for category, sell_cost_str in call_data.items():
                        if "_cost" not in category:
                            provider_cost_details = get_provider_cost_details(
                                category=category
                            )

                            if (
                                provider_cost_details
                                and category in provider_cost_details
                            ):
                                provider_cost = provider_cost_details[category]
                                sell_cost = Decimal(sell_cost_str)
                                total_sell_cost += sell_cost
                                cost_price = Decimal(
                                    call_data.get(f"{category}_cost", "0")
                                )
                                costtb_data = {
                                    "call_log_id": call_log_id,
                                    "provider_id": provider_cost["id"],
                                    "sell_cost": sell_cost,
                                    "cost": cost_price,
                                }
                                insert_new_costtb(costtb_data)

                    balance = Decimal(
                        redis_client.hget(user_balance_key, "balance") or "0"
                    )
                    update_user(user_id=user_id, UserBalance=balance)

                    update_call_log(
                        call_log_id=call_log_id,
                        call_cost=total_sell_cost,
                        call_end_time=call_endtime,
                        call_duration=call_duration,
                        status=call_status,
                    )

                except Exception as e:
                    print(f"Error storing call data for call_log_id {call_log_id}: {e}")
                    print(
                        f"Call data that failed to store: {call_data}, call_key: {call_key}"
                    )
                    raise

            redis_client.delete(call_key)

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
        user = get_user_details(user_id=user_id)
        redis_client.hset(user_balance_key, "balance", str(user["UserBalance"]))

    if not redis_client.exists(call_key):
        for category in provider_costs.keys():
            redis_client.hset(call_key, category, "0")
            redis_client.hset(call_key, f"{category}_cost", "0")

    total_sell_cost_per_5_seconds = sum(
        Decimal(details["sell_price"] / 60 * 5) for details in provider_costs.values()
    )

    is_updated_ring_queued_initiated = False
    is_updated_in_progress = False
    is_updated_queued_initiated = False

    while True:
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            call = client.calls(call_sid).fetch()

            call_endtime = call.end_time
            call_duration = call.duration
            call_status = call.status

            if call_status in ["ringing"]:
                if not is_updated_ring_queued_initiated:

                    update_call_log(call_log_id=call_log_id, status=call_status)
                    is_updated_ring_queued_initiated = True
                    # time.sleep(5)
            elif call_status in ["queued", "initiated"]:
                if not is_updated_queued_initiated:

                    update_call_log(call_log_id=call_log_id, status=call_status)
                    is_updated_queued_initiated = True

            elif call_status == "in-progress":
                if not is_updated_in_progress:
                    update_call_log(
                        call_log_id=call_log_id,
                        status=call_status,
                        call_start_time=call.start_time,
                    )
                    is_updated_in_progress = True

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
                    call.update(status="completed")
                    call_status = "Ended: Balance Low"
                    finalize_call_data(
                        redis_client,
                        user_balance_key,
                        call_key,
                        call_log_id,
                        user_id,
                        call_endtime,
                        call_duration,
                        call_status,
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

            elif call_status in ["canceled", "failed", "no-answer", "busy"]:

                call_endtime = None
                finalize_call_data(
                    redis_client,
                    user_balance_key,
                    call_key,
                    call_log_id,
                    user_id,
                    call_endtime,
                    call_duration,
                    call_status,
                )
                break
            elif call_status in ["completed"]:

                finalize_call_data(
                    redis_client,
                    user_balance_key,
                    call_key,
                    call_log_id,
                    user_id,
                    call_endtime,
                    call_duration,
                    call_status,
                )
                break

            # time.sleep(5)

        except Exception as e:
            print(f"Error while monitoring call {call_sid}: {e}")
            logger.error(f"Monitorrrrr {call_log_id}: {e}")
            break  # Break if there’s an error
