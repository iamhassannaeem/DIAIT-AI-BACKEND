import ast
import os

import regex as re
from dotenv import load_dotenv
from twilio.rest import Client
from dotenv import load_dotenv
# from .DB_functions import insert_or_update_call_details, 

from .finding_answer_of_question import process_answers, extract_user_info
import regex as re 
import asyncio
import datetime
import sys
import django



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from ai_call_agent.models import CallLog, ProviderCost

from django.conf import settings
from authentication.models import User
from config import settings
from ai_call_agent.tasks2 import monitor_call
from ai_call_agent.query import (
   update_call_log,
   update_contact_and_call_log_for_sales,
   insert_feedback_reports

) 




load_dotenv()
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]


def get_qns_with_id_from_data(raw_data, history):


    for question in raw_data['feedback_questions']:
        if isinstance(question, dict):
            question.pop('order', None)
        else:
            pass

    return process_answers(raw_data["feedback_questions"], history)






def put_call_details(call_sid, history, uid=None, raw_data=None):
    
    
    try:

        updated_uid = uid if uid is not None else "None"

        if updated_uid:

            update_call_log(
                    call_log_id=updated_uid, conversation=history,
                    )
            if raw_data and history is not None:
                if raw_data['campaign_type'] == 'Outbound_sales':
                    user_data = extract_user_info(history)
                    update_contact_and_call_log_for_sales(uid, **user_data)
                else:
                    qnas_data = get_qns_with_id_from_data(raw_data, history)
                    insert_feedback_reports(updated_uid, qnas_data)
            else:
                print("Raw data or history is None. Skipping raw data processing.")
        else:
            update_call_log(
                    call_log_id=updated_uid, conversation=history,
                    )

    except Exception as e:
        print(f"Error fetching call details: {e}")

