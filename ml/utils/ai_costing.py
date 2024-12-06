import os
import sys
import django
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_dir = os.path.dirname(BASE_DIR)

sys.path.append(parent_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


from redis import StrictRedis
from ai_call_agent.models import ProviderCost
from django.conf import settings
from .our_redis import pool,StrictRedis


def update_cost_in_redis_for_llm(
    call_sid, user_id,sell_price,cost_price, provider_id=4
):
    
    redis_client = StrictRedis(connection_pool=pool)

    try:
        provider_cost = ProviderCost.objects.get(id=provider_id)

        category = provider_cost.category


        sell_price = round(sell_price, 6)
        cost_price = round(cost_price, 6)

        call_key = f"user_call:{user_id}:{call_sid}"

        redis_client.hincrbyfloat(call_key, f"{category}_sell_price", sell_price)
        redis_client.hincrbyfloat(call_key, f"{category}_cost_price", cost_price)

        redis_client.hset(call_key, f"{category}_category", category)

        print(
            f"Successfully updated Redis for call_sid={call_sid}, user_id={user_id}, provider_id={provider_id}."
        )

    except ProviderCost.DoesNotExist:
        print(f"ProviderCost with id {provider_id} not found.")
    except Exception as e:
        print(
            f"Error updating provider cost in Redis for call_sid={call_sid}, user_id={user_id}: {e}"
        )




def cost_in_thread(call_sid, user_id, sell_price, cost_price, provider_id=4):
    thread = threading.Thread(target=update_cost_in_redis_for_llm, args=(call_sid, user_id, sell_price, cost_price, provider_id))
    thread.start()





# call_sid = "test_call_sid_12345"
# user_id = 1
# sell_price = 0.4
# cost_price = 0.2
# cost_in_thread(call_sid, user_id,sell_price,cost_price)















