# utils.py
from celery import current_app
from celery.exceptions import TaskRevokedError
from celery.result import AsyncResult
from django.core.exceptions import ObjectDoesNotExist
from requests import Response
from rest_framework import status
from twilio.rest import Client

from ai_call_agent.models import Campaign, CallLog
from config import settings


def stop_campaign_task(campaign_id):
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        task_id = campaign.task_id
        twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        if task_id:
            task = AsyncResult(task_id)
            task.revoke(terminate=True)

            campaign.status = 4
            campaign.save()

            print(
                f"Task {task_id} revoked successfully and campaign {campaign_id} status updated to 'Stopped'."
            )
        else:
            print(
                f"No task found for campaign {campaign_id}. Task could not be stopped."
            )
        call_logs = CallLog.objects.filter(campaign_id=campaign_id).exclude(
            call_task_id__isnull=True
        )
        if not call_logs.exists():
            return Response(
                {"message": "No active tasks found for this campaign."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task_ids = call_logs.values_list("call_task_id", flat=True)
        for task_id in task_ids:
            try:
                current_app.control.revoke(task_id, terminate=True)
                print(f"Task {task_id} revoked successfully.")
            except Exception as e:
                print(f"Error revoking task {task_id}: {e}")
        call_sids = call_logs.values_list("call_sid", flat=True)
        for call_sid in call_sids:
            try:
                call = twilio_client.calls(call_sid).update(status="completed")
                print(f"Call {call_sid} stopped successfully.")
            except Exception as e:
                print(f"Error stopping call {call_sid}: {e}")

        call_logs.update(status="stopped")

    except ObjectDoesNotExist:
        print(f"Campaign with ID {campaign_id} does not exist.")
    except TaskRevokedError:
        print(f"Task with ID {task_id} was already revoked.")

    #     campaign = Campaign.objects.get(id=campaign_id)
    #
    #     task_id = campaign.task_id
    #
    #     if task_id:
    #         task = AsyncResult(task_id)
    #         task.revoke(terminate=True)
    #
    #         campaign.status = 4
    #         campaign.save()
    #
    #         print(
    #             f"Task {task_id} revoked successfully and campaign {campaign_id} status updated to 'Stopped'."
    #         )
    #     else:
    #         print(
    #             f"No task found for campaign {campaign_id}. Task could not be stopped."
    #         )
    # except ObjectDoesNotExist:
    #     print(f"Campaign with ID {campaign_id} does not exist.")
    # except TaskRevokedError:
    #     print(f"Task with ID {task_id} was already revoked.")
