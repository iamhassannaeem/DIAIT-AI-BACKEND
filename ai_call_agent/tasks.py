import os
import sys

import django
from celery import shared_task

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from datetime import datetime

from ai_call_agent.models import Campaign, AgentFileMapping
from ml.app import make_call


def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError(f"Object of type {x.__class__.__name__} is not JSON serializable")


@shared_task
def Ai_task(campaign_id):
    campaign = Campaign.objects.filter(id=campaign_id).first()
    print("###################", campaign)
    if campaign:
        campaign.status = 1
        campaign.save()
        if campaign.type == 1:
            campaigns = (
                Campaign.objects.filter(id=campaign_id)
                .select_related("agent__twillio_number")
                .prefetch_related("agent__questions", "call_logs")
            )
        else:
            campaigns = (
                Campaign.objects.filter(id=campaign_id)
                .select_related("agent__twillio_number")
                .prefetch_related("call_logs", "agent__files")
            )

        campaign_data = []
        for campaign in campaigns:
            agent = campaign.agent
            feedback_questions = (
                agent.questions.all() if agent and campaign.type == 1 else []
            )
            twilio_number = agent.twillio_number if agent else None

            files = (
                AgentFileMapping.objects.filter(agent_details=agent)
                .select_related("file")
                .values(
                    "file__id",
                    "file__file_name",
                    "file__file_type",
                    "file__file_size",
                    "file__content_type",
                    "file__created_date",
                    "file_type",
                )
                if agent and campaign.type == 2
                else []
            )

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
                    "status": call.status,
                    "call_cost": str(call.call_cost) if call.call_cost else None,
                }
                for call in campaign.call_logs.all()
            ]

            campaign_info = {
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "campaign_type": campaign.get_type_display(),
                "campaign_status": campaign.get_status_display(),
                "agent": {
                    "user_id": agent.user_id if agent else None,
                    "id": agent.id if agent else None,
                    "name": agent.name if agent else None,
                    "active": agent.active if agent else None,
                    "first_message": (agent.first_message if agent else None),
                    "gender": agent.gender if agent else None,
                    "created_date": (agent.created_date if agent else None),
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
                "call_details": call_details,
                "agent_files": list(files),  # Include file data here
            }

            campaign_data.append(campaign_info)

        print(campaign_data)
        make_call(campaign_info)

        campaign.status = 3
        campaign.save()

    else:
        print(f"No campaign found with ID {campaign_id}")


# @shared_task
# def Ai_task(campaign_id):
#
#     campaign = Campaign.objects.filter(id=campaign_id).first()
#     print("###################", campaign)
#     if campaign:
#         campaign.status = 1
#         campaign.save()
#         if campaign.type == 1:
#             campaigns = (
#                 Campaign.objects.filter(id=campaign_id)
#                 .select_related("agent__twillio_number")
#                 .prefetch_related("agent__questions", "call_logs")
#             )
#         else:
#             campaigns = (
#                 Campaign.objects.filter(id=campaign_id)
#                 .select_related("agent__twillio_number")
#                 .prefetch_related("calls")
#             )
#
#         campaign_data = []
#         for campaign in campaigns:
#             agent = campaign.agent
#             feedback_questions = (
#                 agent.questions.all() if agent and campaign.type == 1 else []
#             )
#             twilio_number = agent.twillio_number if agent else None
#
#             call_details = [
#                 {
#                     "call_id": call.id,
#                     "phone_number": call.phone_number,
#                     "call_start_time": (
#                         call.call_start_time.isoformat()
#                         if call.call_start_time
#                         else None
#                     ),
#                     "call_end_time": (
#                         call.call_end_time.isoformat() if call.call_end_time else None
#                     ),
#                     "conversation": call.conversation,
#                     "status": call.status,
#                     "call_cost": str(call.call_cost) if call.call_cost else None,
#                 }
#                 for call in campaign.call_logs.all()
#             ]
#
#             campaign_info = {
#                 "campaign_id": campaign.id,
#                 "campaign_name": campaign.name,
#                 "campaign_type": campaign.get_type_display(),
#                 "campaign_status": campaign.get_status_display(),
#                 "agent": {
#                     "user_id": agent.user_id if agent else None,
#                     "id": agent.id if agent else None,
#                     "name": agent.name if agent else None,
#                     "active": agent.active if agent else None,
#                     "first_message": (agent.first_message if agent else None),
#                     "gender": agent.gender if agent else None,
#                     "created_date": (agent.created_date if agent else None),
#                     "twillio_number": (
#                         {
#                             "id": twilio_number.id if twilio_number else None,
#                             "phone_number": (
#                                 twilio_number.phone_number if twilio_number else None
#                             ),
#                             "status": twilio_number.status if twilio_number else None,
#                         }
#                         if twilio_number
#                         else None
#                     ),
#                 },
#                 "feedback_questions": [
#                     {
#                         "id": question.id,
#                         "order": question.order,
#                         "question_text": question.question_text,
#                     }
#                     for question in feedback_questions
#                 ],
#                 "call_details": call_details,
#             }
#
#             campaign_data.append(campaign_info)
#
#         print(campaign_data)
#         make_call(campaign_info)
#
#         campaign.status = 3
#         campaign.save()
#
#     else:
#         print(f"No campaign found with ID {campaign_id}")
#
