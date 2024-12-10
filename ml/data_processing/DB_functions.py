import os
import sys

import django
import time 
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils import timezone
from ai_call_agent.models import Campaign, CallLog, Question, Contact





import logging
from django.utils.timezone import now as timezone_now

# Configure the logger
logging.basicConfig(
    filename='call_details.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def insert_or_update_call_details(
    call_id,
    phone_number=None,
    tag=None,
    call_start_time=None,
    call_end_time=None,
    conversation=None,
    status=1,
    call_cost=None,
    campaign_id=None,
    call_duration=None
):
    logger.info("Starting insert_or_update_call_details with call_id: %s", call_id)

    # Get the campaign object if campaign_id is provided
    campaign = None
    if campaign_id:
        try:
            campaign = Campaign.objects.get(id=campaign_id)
            logger.info("Campaign fetched: %s", campaign)
        except Campaign.DoesNotExist:
            logger.error("Campaign with ID %s does not exist", campaign_id)
            campaign = None

    try:
        logger.info("Attempting to fetch CallLog with ID: %s", call_id)
        call_detail = CallLog.objects.get(id=call_id)
        logger.info("CallLog fetched: %s", call_detail)

        # Update call details if parameters are provided
        if phone_number is not None:
            call_detail.phone_number = phone_number
            logger.info("Updated phone number: %s", phone_number)
        if tag is not None:
            call_detail.tag = tag
            logger.info("Updated tag: %s", tag)
        if call_start_time is not None:
            call_detail.call_start_time = call_start_time
            logger.info("Updated call start time: %s", call_start_time)
        if call_end_time is not None:
            call_detail.call_end_time = call_end_time
            logger.info("Updated call end time: %s", call_end_time)
        if call_duration is not None:
            call_detail.call_duration = call_duration
            logger.info("Updated call duration: %s", call_duration)
        if conversation is not None:
            call_detail.conversation = conversation
            logger.info("Updated conversation: %s", conversation)
        if status is not None:
            call_detail.status = status
            logger.info("Updated status: %s", status)
        if call_cost is not None:
            call_detail.call_cost = call_cost
            logger.info("Updated call cost: %s", call_cost)
        if campaign_id is not None:
            call_detail.campaign = campaign
            logger.info("Updated campaign: %s", campaign)

        # Save the updated call details
        logger.info("Saving updated call details")
        call_detail.save()
        logger.info("CallLog successfully updated: %s", call_detail)

    except CallLog.DoesNotExist:
        logger.warning("CallLog does not exist. Creating new CallLog with ID: %s", call_id)

        # Create new call log entry if the specified one doesn't exist
        try:
            call_detail = CallLog.objects.create(
                id=call_id,
                phone_number=phone_number,
                tag=tag,
                call_start_time=call_start_time or timezone_now(),
                call_end_time=call_end_time or timezone_now(),
                conversation=conversation,
                status=status,
                call_cost=call_cost,
                campaign=campaign,
            )
            logger.info("New CallLog created: %s", call_detail)
        except Exception as e:
            logger.error("Error creating CallLog: %s", str(e))
            raise

    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        raise

    logger.info("Function completed successfully with CallLog: %s", call_detail)
    return call_detail







def insert_feedback_reports(call_detail_id, feedback_data):
    logger.info("Starting insert_feedback_reports with call_detail_id: %s", call_detail_id)

    try:
        # Fetch the CallLog object
        logger.info("Attempting to fetch CallLog with ID: %s", call_detail_id)
        call_detail = CallLog.objects.get(id=call_detail_id)
        logger.info("CallLog fetched: %s", call_detail)

        # Prepare content dictionary from feedback_data
        content = {}
        for index, item in enumerate(feedback_data, start=1):
            question_key = f"Q{index}"
            answer_key = f"A{index}"
            question_text = item.get("question_text")
            answer_text = item.get("answer")
            if question_text:
                content[question_key] = question_text
                logger.info("Added question to content: %s -> %s", question_key, question_text)
            if answer_text:
                content[answer_key] = answer_text
                logger.info("Added answer to content: %s -> %s", answer_key, answer_text)

        # Save content to call_detail
        call_detail.content = content
        logger.info("Updated call_detail content: %s", content)
        
        call_detail.save()
        logger.info("CallLog successfully updated with feedback reports: %s", call_detail)

        return "Feedback reports created successfully."

    except CallLog.DoesNotExist:
        logger.error("CallLog with ID %s does not exist.", call_detail_id)
        raise ValueError("CallLog with the given ID does not exist.")

    except Exception as e:
        logger.error("Unexpected error in insert_feedback_reports: %s", str(e))
        raise



    




from django.db import transaction


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



# feedback_data = [{'id': 19, 'question_text': 'How was Your experience at our Restaurant?', 'answer': 'Not answered'}, {'id': 20, 'question_text': 'Which Food Do You like the Most?', 'answer': 'Not answered'}, {'id': 21, 'question_text': 'Is there any thing you want us  to update?', 'answer': 'Not answered'}]
# call_id = 294
# insert_feedback_reports(call_id , feedback_data)