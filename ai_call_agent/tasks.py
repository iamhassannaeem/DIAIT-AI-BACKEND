import json
from datetime import datetime

from celery import shared_task

from .models import Campaign


def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError(f"Object of type {x.__class__.__name__} is not JSON serializable")


@shared_task
def perform_campaign_task(campaign_id):

    print(f"Performing job for campaign with ID {campaign_id}")


@shared_task
def Ai_task(campaign_id):

    campaign = Campaign.objects.filter(id=campaign_id).first()

    if campaign:

        campaign.status = 1
        campaign.save()

        campaigns = (
            Campaign.objects.filter(id=campaign_id)
            .select_related("feedback_agent__twillio_number")
            .prefetch_related("feedback_agent__feed_questions", "calls")
        )

        campaign_data = []
        for campaign in campaigns:
            feedback_agent = campaign.feedback_agent
            feedback_questions = (
                feedback_agent.feed_questions.all() if feedback_agent else []
            )
            twilio_number = feedback_agent.twillio_number if feedback_agent else None

            # Fetch related call details for the campaign
            call_details = [
                {
                    "call_id": call.id,
                    "phone_number": call.phone_number,
                    "call_start_time": (
                        call.call_start_time.isoformat()
                        if call.call_start_time
                        else None
                    ),
                    "call_end_time": (
                        call.call_end_time.isoformat() if call.call_end_time else None
                    ),
                    "conversation": call.conversation,
                    "status": call.get_status_display(),
                    "call_cost": str(call.call_cost) if call.call_cost else None,
                }
                for call in campaign.calls.all()
            ]

            campaign_info = {
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "campaign_type": campaign.get_type_display(),
                "campaign_status": campaign.get_status_display(),
                "feedback_agent": {
                    "id": feedback_agent.id if feedback_agent else None,
                    "name": feedback_agent.name if feedback_agent else None,
                    "active": feedback_agent.active if feedback_agent else None,
                    "first_message": (
                        feedback_agent.first_message if feedback_agent else None
                    ),
                    "gender": feedback_agent.gender if feedback_agent else None,
                    "created_date": (
                        feedback_agent.created_date if feedback_agent else None
                    ),
                    "twillio_number": (
                        {
                            "id": twilio_number.id if twilio_number else None,
                            "phone_number": (
                                twilio_number.phone_number if twilio_number else None
                            ),
                            "status": twilio_number.status if twilio_number else None,
                        }
                        if twilio_number
                        else None
                    ),
                },
                "feedback_questions": [
                    {
                        "id": question.id,
                        "order": question.order,
                        "question_text": question.question_text,
                    }
                    for question in feedback_questions
                ],
                "call_details": call_details,  # Add call details here
            }
            campaign_data.append(campaign_info)

        campaign_data_json = json.dumps(
            campaign_data, default=datetime_handler, indent=4
        )
        abdul(campaign_data_json)
    else:
        print(f"No campaign found with ID {campaign_id}")


def abdul(jason):

    print("Received JSON data:", jason)
