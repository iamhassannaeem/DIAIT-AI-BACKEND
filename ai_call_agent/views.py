# import os
# import sys
# from datetime import datetime
#
# import pytz
# from django.core.management import execute_from_command_line
# from djang
#
# os.environ.setdefault(
#     "DJANGO_SETTINGS_MODULE", config.settings
# )  # Make sure this is set correctly
# execute_from_command_line(sys.argv)
#
# # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# # import django
#
# # django.setup()
#
#
# def schedule_task():
#     schedule_time = "2024-11-08T14:34:00Z"
#     timezone_str = "utc"
#
#     try:
#         # Handle the UTC "Z" by replacing it with the UTC offset
#         if schedule_time.endswith("Z"):
#             schedule_time = schedule_time.replace("Z", "+00:00")
#
#         # Parse the datetime string into a timezone-aware datetime object
#         schedule_dt = datetime.fromisoformat(schedule_time)
#     except ValueError:
#         return JsonResponse({"error": "Invalid datetime format"}, status=400)
#
#     # Ensure the datetime is timezone-aware
#     if is_naive(schedule_dt):
#         # If the datetime is naive, make it aware
#         try:
#             # Convert the datetime to the specified timezone
#             schedule_dt = make_aware(schedule_dt, pytz.timezone(timezone_str.lower()))
#         except pytz.UnknownTimeZoneError:
#             return JsonResponse({"error": "Invalid timezone."}, status=400)
#
#     # Get the current UTC time
#     current_utc_time = datetime.now(pytz.UTC)
#
#     # Check if the scheduled time is in the past
#     if schedule_dt < current_utc_time:
#         return JsonResponse(
#             {"error": "Scheduled time cannot be in the past."}, status=400
#         )
#
#     # Print for debugging (optional)
#     print(f"Scheduled datetime: {schedule_dt}")
#
#     # Schedule the task with the calculated eta (scheduled time)
#     # task = perform_campaign_task.apply_async((), eta=schedule_dt)
#
#     # # Save the task id to the campaign model
#     # campaign.task_id = task.id
#     # campaign.save()
#
#
# schedule_task()
