import os
import django
import sys
import asyncio

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  
django.setup()

from django.utils import timezone
from ai_call_agent.models import Campaign, CallLog,Question




def insert_or_update_call_details(call_id, phone_number = None, tag=None, call_start_time=None, call_end_time=None, conversation=None, status=1, call_cost=None, campaign_id=None):
    campaign = Campaign.objects.get(id=campaign_id) if campaign_id else None

    try:
        call_detail = CallLog.objects.get(id=call_id)
        print(call_id)
        if phone_number is not None:
            call_detail.phone_number = phone_number
        if tag is not None:
            call_detail.tag = tag
        if call_start_time is not None:
            call_detail.call_start_time = call_start_time
        if call_end_time is not None:
            call_detail.call_end_time = call_end_time
        if conversation is not None:
            call_detail.conversation = conversation
        if status is not None:
            call_detail.status = status
        if call_cost is not None:
            call_detail.call_cost = call_cost
        if campaign_id is not None:
            call_detail.campaign = campaign

        call_detail.save()
       
    except CallLog.DoesNotExist:
        call_detail = CallLog.objects.create(
            id=call_id,
            phone_number=phone_number,
            tag=tag,
            call_start_time=call_start_time or timezone.now(),
            call_end_time=call_end_time or timezone.now(),
            conversation=conversation,
            status=status,
            call_cost=call_cost,
            campaign=campaign
        )
   
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
        print(content)
        call_detail.save()

        return "Feedback reports created successfully."

    except CallLog.DoesNotExist:
        raise ValueError("CallLog with the given ID does not exist.")

    
