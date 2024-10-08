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

class Provider(models.Model):
    provider_name = models.CharField(max_length=100)

    def __str__(self):
        return self.provider_name

class File(models.Model):
    file_name = models.CharField(max_length=100)

    def __str__(self):
        return self.file_name
class FeedBackAgent(models.Model):
    feedback_id = models.AutoField(primary_key=True)  # Automatically incremented ID
    questions = models.TextField()  # Field for feedback questions

    def __str__(self):
        return f"Feedback {self.feedback_id}: {self.questions[:20]}"  # Display first 20 chars


class AgentDetails(models.Model):
    agent_name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use AUTH_USER_MODEL here
    agent_type = models.ForeignKey(Agent, on_delete=models.CASCADE)
    model_type = models.ForeignKey(ModelType, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    created_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)
    del_date = models.DateTimeField(null=True, blank=True)
    prompt_files = models.ForeignKey(File, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} - {self.agent_name}"




