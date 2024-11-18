
import os
import django
import sys
import asyncio
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  
django.setup()
import json
from datetime import datetime
from celery import shared_task, current_task



# from django.conf import settings
from authentication.models import User
from config import settings
from ai_call_agent.models import Campaign
from django.contrib.sessions.models import Session
from decimal import Decimal



from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()
account_sid = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']

def stop_call_for_low_balance(call_sid):
    client = Client(account_sid, TWILIO_AUTH_TOKEN)
    call = client.calls(call_sid).update(status='completed')



def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError(f"Object of type {x.__class__.__name__} is not JSON serializable")


@shared_task
def monitor_call(user_id, call_sid):
    session = Session()
    user = User.objects.get(id = user_id)

    
    per_second_cost = (settings.SERVER_COST +settings.OPENAI_COST +settings.DEEPGRAM_COST +settings.TWILIO_COST) / 60

    elapsed_time = 5
    cost = Decimal(per_second_cost) * Decimal(elapsed_time)  
    user.UserBalance -= cost
    user.save()

    if user.UserBalance < cost:
        stop_call_for_low_balance(call_sid)
        print("Call terminated due to insufficient credits.")
       
        return "Call ended due to low balance."





# Redis_list = [0, 0, 0, 0]

# def costing():
#     Redis_list[0] += settings.SERVER_COST
#     Redis_list[1] += settings.OPENAI_COST
#     Redis_list[2] += settings.DEEPGRAM_COST
#     Redis_list[3] += settings.TWILIO_COST


# def total_cost():
#     print(sum(Redis_list))
# costing()
# print(Redis_list)
# costing()
# print(Redis_list)
# costing()
# print(Redis_list)


# total_cost()


