from django.shortcuts import render, redirect
from django.http import HttpResponse
from ..models import AgentDetails, Agent, ModelType, tech_Provider, Num_Provider, File
from authentication.models import TwilioNumbers
from django.urls import reverse
from django.http import HttpResponseRedirect


def add_agent_details(request, user_id):
    if request.method == 'POST':

        agent_name = request.POST.get('agent_name')
        agent_type_id = request.POST.get('agent_type')
        model_type_id = request.POST.get('model_type')
        first_message = request.POST.get('first_message')
        technology_provider_id = request.POST.get('technology_provider')
        phone_number_provider_id = request.POST.get('phone_number_provider')
        prompt_files_id = request.POST.get('prompt_files')
        agent_status = request.POST.get('agent_status', 'active')


        agent_details = AgentDetails.objects.create(
            agent_name=agent_name,
            user_id=user_id,
            agent_type_id=agent_type_id,
            model_type_id=model_type_id,
            first_message=first_message,
            technology_provider_id=technology_provider_id,
            phone_number_provider_id=phone_number_provider_id,
            prompt_files_id=prompt_files_id,
            agent_status=agent_status
        )


        return redirect('select_phone_number', agent_id=agent_details.id)

    else:

        agents = Agent.objects.all()
        model_types = ModelType.objects.all()
        tech_providers = tech_Provider.objects.all()
        num_providers = Num_Provider.objects.all()
        prompt_files = File.objects.all()

    return render(request, 'add_agent_details.html', {
        'agents': agents,
        'model_types': model_types,
        'tech_providers': tech_providers,
        'num_providers': num_providers,
        'prompt_files': prompt_files,
        'user_id': user_id
    })


def select_phone_number(request, agent_id):
    agent_details = AgentDetails.objects.get(id=agent_id)
    user_id = agent_details.user_id
    phone_numbers = TwilioNumbers.objects.filter(user_id=user_id)

    if request.method == 'POST':
        selected_phone_number = request.POST.get('phone_number')


        agent_details.phone_number = selected_phone_number
        agent_details.save()


        return redirect('success')

    return render(request, 'select_phone_number.html', {
        'phone_numbers': phone_numbers,
        'agent_details': agent_details
    })



def success_view(request):
    return render(request, 'success.html')