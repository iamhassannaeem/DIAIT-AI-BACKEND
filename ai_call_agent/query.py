import logging
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from ai_call_agent.models import Campaign, Contact, CallLog, Costtb, ProviderCost
from authentication.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("db_query_logs.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def get_contact_by_id(contact_id):
    try:
        contact = Contact.objects.get(id=contact_id)
        logger.info(f"Fetched Contact: {contact}")
        return contact
    except Contact.DoesNotExist:
        logger.error(f"Contact with ID {contact_id} does not exist.")
        return None


def get_campaign_by_id(campaign_id):
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        logger.info(f"Fetched Campaign: {campaign}")
        return campaign
    except Campaign.DoesNotExist:
        logger.error(f"Campaign with ID {campaign_id} does not exist.")
        return None


def get_call_log(call_log_id=None, **filters):
    try:
        if call_log_id:

            call_log = CallLog.objects.get(id=call_log_id)
            logger.info(f"Retrieved CallLog record with ID {call_log_id}.")
            return call_log
        else:
            call_logs = CallLog.objects.filter(**filters)
            logger.info(
                f"Retrieved {call_logs.count()} CallLog records with filters {filters}."
            )
            return call_logs
    except CallLog.DoesNotExist:
        logger.error(f"CallLog record with ID {call_log_id} not found.")
        return None
    except Exception as e:
        logger.error(f"An error occurred while retrieving CallLog records: {str(e)}")
        return None


def get_provider_cost_details(provider_id=None, **filters):
    try:
        if provider_id:
            provider = ProviderCost.objects.get(id=provider_id)
            return {
                provider.category: {
                    "sell_price": Decimal(provider.sell_price),
                    "cost_price": Decimal(provider.cost_price),
                    "provider": provider.provider,
                    "id": provider.id,
                }
            }
        else:
            providers = ProviderCost.objects.filter(**filters)
            provider_details = {}
            for provider in providers:
                provider_details[provider.category] = {
                    "sell_price": Decimal(provider.sell_price),
                    "cost_price": Decimal(provider.cost_price),
                    "provider": provider.provider,
                    "id": provider.id,
                }
            return provider_details
    except ProviderCost.DoesNotExist:
        logger.error(
            "ProviderCost record with the provided ID or filter does not exist."
        )
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching provider cost details: {str(e)}")
        return None


def get_user_details(user_id=None, **filters):
    try:
        if user_id:
            user = get_user_model().objects.get(id=user_id)
            user_details = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "UserBalance": user.UserBalance,
            }
            return user_details
        else:
            users = get_user_model().objects.filter(**filters)
            user_details_list = []
            for user in users:
                user_details = {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "UserBalance": user.UserBalance,
                }
                user_details_list.append(user_details)
            return user_details_list
    except get_user_model().DoesNotExist:
        logger.error("User record with the provided ID or filter does not exist.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching user details: {str(e)}")
        return None


def update_campaign(campaign_id, **kwargs):
    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"Campaign record with ID {campaign_id} not found.")
        return False

    for field, value in kwargs.items():
        if hasattr(campaign, field):
            setattr(campaign, field, value)
        else:
            logger.warning(f"Field {field} does not exist in Campaign model.")

    try:
        campaign.save()
        logger.info(f"Campaign record ID {campaign_id} updated successfully.")
        return True
    except Exception as e:
        logger.error(f"Error saving Campaign with ID {campaign_id}: {e}")
        return False


def update_contact_and_call_log_for_sales(call_log_id, **contact_data):
    try:
        with transaction.atomic():
            call_log = CallLog.objects.get(id=call_log_id)
            phone_number = call_log.phone_number
            contact, created = Contact.objects.get_or_create(
                phone_number=phone_number, defaults=contact_data
            )
            call_log.contact = contact
            call_log.save()

        return True
    except CallLog.DoesNotExist:
        logger.error(f"CallLog with id {call_log_id} does not exist.")
        return False
    except Exception as e:
        logger.error(f"Error in updating contact and call log for sales: {e}")
        return False


def update_contact(contact_id, **kwargs):
    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        logger.error(f"Contact record with ID {contact_id} not found.")
        return False

    for field, value in kwargs.items():
        if hasattr(contact, field):
            setattr(contact, field, value)
        else:
            logger.warning(f"Field {field} does not exist in Contact model.")

    try:
        contact.save()
        logger.info(f"Contact record ID {contact_id} updated successfully.")
        return True
    except Exception as e:
        logger.error(f"Error saving Contact with ID {contact_id}: {e}")
        return False


def insert_new_contact(contact_data):
    try:
        new_contact = Contact.objects.create(
            phone_number=contact_data.get("phone_number"),
            full_name=contact_data.get("full_name"),
            email=contact_data.get("email"),
            address=contact_data.get("address"),
            date_of_birth=contact_data.get("date_of_birth"),
            tag=contact_data.get("tag"),
        )
        logger.info(f"Inserted new Contact with ID {new_contact.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to insert new Contact: {str(e)}")
        return False


def update_call_log(call_log_id, **kwargs):
    try:
        call_log = CallLog.objects.get(id=call_log_id)
    except CallLog.DoesNotExist:
        logger.error(f"CallLog record with ID {call_log_id} not found.")
        return False

    for field, value in kwargs.items():
        if hasattr(call_log, field):
            setattr(call_log, field, value)
        else:
            logger.warning(f"Field {field} does not exist in CallLog model.")

    try:
        call_log.save()
        logger.info(f"CallLog record ID {call_log_id} updated successfully.")
        return True
    except Exception as e:
        logger.error(f"Error saving CallLog with ID {call_log_id}: {e}")
        return False


def insert_feedback_reports(call_detail_id, feedback_data):
    logger.info(
        "Starting insert_feedback_reports with call_detail_id: %s", call_detail_id
    )
    try:
        call_detail = CallLog.objects.get(id=call_detail_id)
        logger.info("Fetched CallLog: %s", call_detail)

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

        updated_call_log = update_call_log(call_detail_id, content=content)
        if updated_call_log:
            logger.info("Successfully updated CallLog with feedback reports.")
            return True
        else:
            logger.error("Failed to update CallLog with feedback reports.")
            return False
    except CallLog.DoesNotExist:
        logger.error("CallLog with ID %s does not exist.", call_detail_id)
        return False
    except Exception as e:
        logger.error("Unexpected error in insert_feedback_reports: %s", str(e))
        return False


def insert_new_costtb(costtb_data):
    try:
        new_costtb = Costtb.objects.create(
            call_log_id=costtb_data.get("call_log_id"),
            provider_id=costtb_data.get("provider_id"),
            sell_cost=costtb_data.get("sell_cost"),
            cost=costtb_data.get("cost"),
        )
        logger.info(f"Inserted new Costtb with ID {new_costtb.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to insert new Costtb: {str(e)}")
        return False


def update_user(user_id, **kwargs):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found.")
        return False

    for field, value in kwargs.items():
        if hasattr(user, field):
            setattr(user, field, value)
        else:
            logger.warning(f"Field {field} does not exist in User model.")

    try:
        user.save()
        logger.info(f"User record ID {user_id} updated successfully.")
        return True
    except Exception as e:
        logger.error(f"Error saving User with ID {user_id}: {e}")
        return False
