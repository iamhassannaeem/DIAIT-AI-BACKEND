from django.db import models


from django.conf import settings
class Agent(models.Model):
    agent_name = models.CharField(max_length=100)

    def __str__(self):
        return self.agent_name

class ModelType(models.Model):
    model_name = models.CharField(max_length=100)

    def __str__(self):
        return self.model_name

class tech_Provider(models.Model):
    provider_name = models.CharField(max_length=100)

    def __str__(self):
        return self.provider_name
class Num_Provider(models.Model):
    provider_name = models.CharField(max_length=100)

    def __str__(self):
        return self.provider_name
class File(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=100)

    def __str__(self):
        return self.file_name
class FeedBackAgent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    feedback_id = models.AutoField(primary_key=True)
    questions = models.TextField()

    def __str__(self):
        return f"Feedback {self.feedback_id}: {self.questions[:20]}"



class AgentDetails(models.Model):
    AGENT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]

    agent_name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    agent_type = models.ForeignKey(Agent, on_delete=models.CASCADE)
    model_type = models.ForeignKey(ModelType, on_delete=models.CASCADE)
    first_message = models.CharField(max_length=100)
    technology_provider = models.ForeignKey(tech_Provider, on_delete=models.CASCADE)
    phone_number_provider = models.ForeignKey(Num_Provider, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)
    del_date = models.DateTimeField(null=True, blank=True)
    prompt_files = models.ForeignKey(File, on_delete=models.CASCADE)
    agent_status = models.CharField(max_length=10, choices=AGENT_STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.agent_name} - {self.agent_status}"





