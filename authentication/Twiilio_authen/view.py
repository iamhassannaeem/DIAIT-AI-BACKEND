from django.shortcuts import render, redirect
from twilio.rest import Client
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from ..models import TwilioNumbers

User = get_user_model()

def verify_twilio(request):
    if request.method == 'POST':
        account_sid = request.POST.get('account_sid')
        auth_token = request.POST.get('auth_token')
        phone_number = request.POST.get('phone_number')
        user_id = request.POST.get('user_id')

        try:
            client = Client(account_sid, auth_token)
            number = client.lookups.v1.phone_numbers(phone_number).fetch()

            user = User.objects.get(id=user_id)

            if TwilioNumbers.objects.filter(user=user, phone_number=phone_number).exists():
                return JsonResponse({'error': 'Phone number already exists.'})


            twilio_number = TwilioNumbers(
                user=user,
                phone_number=phone_number,
                account_sid=account_sid,
                account_auth_token=auth_token ,
                auth_token_label=user.name
            )
            twilio_number.save()

            return redirect('list_twilio_numbers', user_id=user.id)

        except Exception as e:
            return JsonResponse({'error': str(e)})

    return render(request, 'verify_twilio.html')

def list_twilio_numbers(request, user_id):

    user_twilio_numbers = TwilioNumbers.objects.filter(user_id=user_id)

    return render(request, 'list_twilio_numbers.html', {
        'twilio_numbers': user_twilio_numbers,
        'user_id': user_id
    })
