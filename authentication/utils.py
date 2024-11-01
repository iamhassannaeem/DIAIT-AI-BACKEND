from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client


def send_email(subject, message, recipient_list):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )


def send_verification_code(phone_number, verification_code):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f"Your verification code is: {verification_code}",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone_number,
    )
    return message.sid
