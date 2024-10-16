

from twilio.rest import Client

from django.core.mail import send_mail
from django.conf import settings

def send_email(subject, message, recipient_list):
    """
    Sends an email using the default from email specified in settings.

    :param subject: Subject of the email
    :param message: Body of the email
    :param recipient_list: List of recipient email addresses
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
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
