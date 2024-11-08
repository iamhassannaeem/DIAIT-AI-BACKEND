# utils.py

from celery.exceptions import TaskRevokedError
from celery.result import AsyncResult
from django.core.exceptions import ObjectDoesNotExist

from ai_call_agent.models import Campaign


def stop_campaign_task(campaign_id):
    try:
        # Get the campaign by ID
        campaign = Campaign.objects.get(id=campaign_id)

        # Get the task associated with this campaign
        task_id = campaign.task_id

        # Revoke the task (stop it if it is still running)
        if task_id:
            task = AsyncResult(task_id)
            task.revoke(terminate=True)  # Forcefully terminate the task if it's running

            # Update the campaign status to "Stopped" (status = 4)
            campaign.status = 4
            campaign.save()

            print(
                f"Task {task_id} revoked successfully and campaign {campaign_id} status updated to 'Stopped'."
            )
        else:
            print(
                f"No task found for campaign {campaign_id}. Task could not be stopped."
            )
    except ObjectDoesNotExist:
        print(f"Campaign with ID {campaign_id} does not exist.")
    except TaskRevokedError:
        print(f"Task with ID {task_id} was already revoked.")
