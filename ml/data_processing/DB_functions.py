import os
import sys

import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils import timezone
from ai_call_agent.models import Campaign, CallLog, Question, Contact




# def insert_or_update_call_details(call_id, phone_number = None, tag=None, call_start_time=None, call_end_time=None, conversation=None, status=1, call_cost=None, campaign_id=None, call_duration=None):
#     print("insert or update call details ",call_id, phone_number, tag, call_start_time, call_end_time, conversation, status, call_cost, campaign_id, call_duration)
#     campaign = Campaign.objects.get(id=campaign_id) if campaign_id else None

#     try:
#         call_detail = CallLog.objects.get(id=call_id)
#         # print(call_id)
#         if phone_number is not None:
#             call_detail.phone_number = phone_number
#         if tag is not None:
#             call_detail.tag = tag
#         if call_start_time is not None:
#             call_detail.call_start_time = call_start_time
#         if call_end_time is not None:
#             call_detail.call_end_time = call_end_time
#         if call_duration is not None:
#             call_detail.call_duration = call_duration
#         if conversation is not None:   
#             call_detail.conversation = conversation
#         if status is not None:
#             call_detail.status = status
#         if call_cost is not None:
#             call_detail.call_cost = call_cost
#         if campaign_id is not None:
#             call_detail.campaign = campaign

#         print("call details ",call_detail)
        
#         call_detail.save()

#     except CallLog.DoesNotExist:

#         call_detail = CallLog.objects.create(
#             id=call_id,
#             phone_number=phone_number,
#             tag=tag,
#             call_start_time=call_start_time or timezone.now(),
#             call_end_time=call_end_time or timezone.now(),
#             conversation=conversation,
#             status=status,
#             call_cost=call_cost,
#             campaign=campaign,
#         )
#         print("call details exception ",call_detail)

#     return call_detail


def insert_or_update_call_details(call_id, phone_number = None, tag=None, call_start_time=None, call_end_time=None, conversation=None, status=1, call_cost=None, campaign_id=None, call_duration=None):
    print("@@@@@@@@@@@@@@ insert or update call details ", call_id, phone_number, tag, call_start_time, call_end_time, conversation, status, call_cost, campaign_id, call_duration)
    
    # Get the campaign object if campaign_id is provided
    campaign = Campaign.objects.get(id=campaign_id) if campaign_id else None
    print("@@@@@@@@@@@@@@ Campaign fetched: ", campaign)

    try:
        print("@@@@@@@@@@@@@@ Attempting to fetch CallLog with ID: ", call_id)
        call_detail = CallLog.objects.get(id=call_id)
        print("@@@@@@@@@@@@@@ CallLog fetched: ", call_detail)

        # Update call details if parameters are provided
        if phone_number is not None:
            call_detail.phone_number = phone_number
            print("@@@@@@@@@@@@@@ Updated phone number: ", phone_number)
        if tag is not None:
            call_detail.tag = tag
            print("@@@@@@@@@@@@@@ Updated tag: ", tag)
        if call_start_time is not None:
            call_detail.call_start_time = call_start_time
            print("@@@@@@@@@@@@@@ Updated call start time: ", call_start_time)
        if call_end_time is not None:
            call_detail.call_end_time = call_end_time
            print("@@@@@@@@@@@@@@ Updated call end time: ", call_end_time)
        if call_duration is not None:
            call_detail.call_duration = call_duration
            print("@@@@@@@@@@@@@@ Updated call duration: ", call_duration)
        if conversation is not None:   
            call_detail.conversation = conversation
            print("@@@@@@@@@@@@@@ Updated conversation: ", conversation)
        if status is not None:
            call_detail.status = status
            print("@@@@@@@@@@@@@@ Updated status: ", status)
        if call_cost is not None:
            call_detail.call_cost = call_cost
            print("@@@@@@@@@@@@@@ Updated call cost: ", call_cost)
        if campaign_id is not None:
            call_detail.campaign = campaign
            print("@@@@@@@@@@@@@@ Updated campaign: ", campaign)

        # Save the updated call details
        print("@@@@@@@@@@@@@@ Saving updated call details: ", call_detail)
        call_detail.save()

    except CallLog.DoesNotExist:
        print("@@@@@@@@@@@@@@ CallLog does not exist. Creating new CallLog with ID: ", call_id)
        
        # Create new call log entry if the specified one doesn't exist
        call_detail = CallLog.objects.create(
            id=call_id,
            phone_number=phone_number,
            tag=tag,
            call_start_time=call_start_time or timezone.now(),
            call_end_time=call_end_time or timezone.now(),
            conversation=conversation,
            status=status,
            call_cost=call_cost,
            campaign=campaign,
        )
        print("@@@@@@@@@@@@@@ New CallLog created: ", call_detail)

    return call_detail










def insert_feedback_reports(call_detail_id, feedback_data):
    try:

        call_detail = CallLog.objects.get(id=call_detail_id)
        content = {}

        for index, item in enumerate(feedback_data, start=1):
            question_key = f"Q{index}"
            answer_key = f"A{index}"
            question_text = item.get("question_text")
            answer_text = item.get("answer")
            if question_text:
                content[question_key] = question_text
            if answer_text:
                content[answer_key] = answer_text
        call_detail.content = content
        print("call_detail in insert feedback report", call_detail)

        
        call_detail.save()

        return "Feedback reports created successfully."

    except CallLog.DoesNotExist:
        raise ValueError("CallLog with the given ID does not exist.")



    




from django.db import transaction
#   contact_data = { "email": "example@example.com", "address": "123 Example Street", "date_of_birth": "1990-01-01", "tag": "Important"}
# contact_data = {"email": None, "address": None, "date_of_birth": "2000-12-29", "tag": "Neutral"}


def update_contact_and_call_log_for_sales(call_log_id, **contact_data):
    try:
        with transaction.atomic():
            call_log = CallLog.objects.get(id=call_log_id)
            phone_number = call_log.phone_number
            contact, created = Contact.objects.get_or_create(
                phone_number=phone_number,
                defaults=contact_data  # Only used if creating a new Contact 

            )
            call_log.contact = contact
            call_log.save()
           
            return contact  # Return the Contact instance (newly created or existing)
    except CallLog.DoesNotExist:
        print(f"CallLog with id {call_log_id} does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



feedback_data = [{'id': 19, 'question_text': 'How was Your experience at our Restaurant?', 'answer': 'Not answered'}, {'id': 20, 'question_text': 'Which Food Do You like the Most?', 'answer': 'Not answered'}, {'id': 21, 'question_text': 'Is there any thing you want us  to update?', 'answer': 'Not answered'}]
call_id = 294
insert_feedback_reports(call_id , feedback_data)