import ast
import os

import regex as re
from dotenv import load_dotenv
from twilio.rest import Client
from dotenv import load_dotenv
from .DB_functions import insert_or_update_call_details, insert_feedback_reports , update_contact_and_call_log_for_sales
from .finding_answer_of_question import process_answers, extract_user_info
import regex as re 
import asyncio
import datetime
import ast

load_dotenv()
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]


# def preprocess_datetime_str(data_str):
#     datetime_pattern = r'datetime\.datetime\(([^)]+)\)'
#     return re.sub(datetime_pattern, lambda m: f'"{eval("datetime.datetime(" + m.group(1) + ")").isoformat()}"', data_str)


def get_qns_with_id_from_data(raw_data, history):


    for question in raw_data['feedback_questions']:
        if isinstance(question, dict):
            question.pop('order', None)
        else:
            pass
            # print(f"Expected a dictionary but got: {type(question)}")

    return process_answers(raw_data["feedback_questions"], history)


# def fetch_call_details(call_sid, history, uid=None, raw_data=None):


#         client = Client(account_sid, TWILIO_AUTH_TOKEN)
#         try:
#             call = client.calls(call_sid).fetch()
#             updated_uid = uid if uid is not None else "None"
#             if updated_uid:
#                 insert_or_update_call_details(
#                     call_id=updated_uid,
#                     phone_number=call.to,
#                     call_start_time=call.start_time,
#                     call_end_time=call.end_time,
#                     call_duration=call.duration,
#                     conversation=history,
#                     status=call.status,
#                 )
#                 if raw_data and history is not None:
#                     if raw_data['campaign_type'] == 'Outbound_sales':
#                         user_data = extract_user_info(history)
#                         update_contact_and_call_log_for_sales(uid , **user_data)

#                     else:
#                         qnas_data = get_qns_with_id_from_data(raw_data , history)
#                         insert_feedback_reports(updated_uid, qnas_data)

#                 else:
#                     pass

#             else:
#                 insert_or_update_call_details(
#                     phone_number=call.to,
#                     call_start_time=call.start_time,
#                     call_end_time=call.end_time,
#                     call_duration=call.duration,
#                     conversation=history,
#                     status=call.status,
#                 )
#             print(f"Call details processed and saved for Call SID: {call_sid}")

#         except Exception as e:
#             print(f"Error fetching call details: {e}")






def fetch_call_details(call_sid, history, uid=None, raw_data=None):
    print("Starting the fetch_call_details function.")
    
    client = Client(account_sid, TWILIO_AUTH_TOKEN)
    print(f"Twilio client initialized with SID: {account_sid}")
    
    try:
        print(f"Fetching details for call SID: {call_sid}")
        call = client.calls(call_sid).fetch()
        print(f"Fetched call details: {call.to}, {call.start_time}, {call.end_time}, {call.duration}, {call.status}")

        updated_uid = uid if uid is not None else "None"
        print(f"Updated UID: {updated_uid}")

        if updated_uid:
            print("Proceeding to insert or update call details.")
            insert_or_update_call_details(
                call_id=updated_uid,
                phone_number=call.to,
                call_start_time=call.start_time,
                call_end_time=call.end_time,
                call_duration=call.duration,
                conversation=history,
                status=call.status,
            )
            print(f"Call details inserted/updated for UID: {updated_uid}")

            if raw_data and history is not None:
                print("Processing raw data and history.")
                if raw_data['campaign_type'] == 'Outbound_sales':
                    print("Campaign type is 'Outbound_sales'. Extracting user info.")
                    user_data = extract_user_info(history)
                    update_contact_and_call_log_for_sales(uid, **user_data)
                    print(f"Sales user data updated for UID: {uid}")
                else:
                    print("Campaign type is not 'Outbound_sales'. Processing Q&A data.")
                    qnas_data = get_qns_with_id_from_data(raw_data, history)
                    print("#########################################33333",qnas_data)
                    insert_feedback_reports(updated_uid, qnas_data)
                    print(f"Feedback reports inserted for UID: {updated_uid}")
            else:
                print("Raw data or history is None. Skipping raw data processing.")
        else:
            print("No updated UID. Proceeding to insert call details without a UID.")
            insert_or_update_call_details(
                phone_number=call.to,
                call_start_time=call.start_time,
                call_end_time=call.end_time,
                call_duration=call.duration,
                conversation=history,
                status=call.status,
            )
            print(f"Call details inserted for phone number: {call.to}")

        print(f"Call details processed and saved for Call SID: {call_sid}")

    except Exception as e:
        print(f"Error fetching call details: {e}")

