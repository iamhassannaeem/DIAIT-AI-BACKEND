import ast
import os

import regex as re
from dotenv import load_dotenv
from twilio.rest import Client

from .DB_functions import insert_or_update_call_details, insert_feedback_reports
from .finding_answer_of_question import process_answers

load_dotenv()
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]


def preprocess_datetime_str(data_str):
    datetime_pattern = r"datetime\.datetime\(([^)]+)\)"
    return re.sub(
        datetime_pattern,
        lambda m: f'"{eval("datetime.datetime(" + m.group(1) + ")").isoformat()}"',
        data_str,
    )


def get_qns_with_id_from_data(raw_data, history):
    raw_data = preprocess_datetime_str(raw_data)
    raw_data = ast.literal_eval(raw_data)
    for question in raw_data["feedback_questions"]:
        if isinstance(question, dict):  # Check if question is a dictionary
            question.pop("order", None)
        else:
            pass
            # print(f"Expected a dictionary but got: {type(question)}")

    return process_answers(raw_data["feedback_questions"], history)


def fetch_call_details(call_sid, history, uid=None, raw_data=None):
    client = Client(account_sid, TWILIO_AUTH_TOKEN)
    try:
        call = client.calls(call_sid).fetch()
        updated_uid = uid if uid is not None else "None"
        if updated_uid:
            insert_or_update_call_details(
                call_id=updated_uid,
                phone_number=call.to,
                call_start_time=call.start_time,
                call_end_time=call.end_time,
                conversation=history,
                status=call.status,
            )
            if raw_data:
                qnas_data = get_qns_with_id_from_data(raw_data, history)
                insert_feedback_reports(updated_uid, qnas_data)
            else:
                pass

        else:
            insert_or_update_call_details(
                phone_number=call.to,
                call_start_time=call.start_time,
                call_end_time=call.end_time,
                conversation=history,
                status=call.status,
            )
        # print(f"Call details processed and saved for Call SID: {call_sid}")

    except Exception as e:
        print(f"Error fetching call details: {e}")
