from django.db import models
from django.conf import settings

class TwilioNumbers(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    account_sid = models.CharField(max_length=100)
    account_auth_token = models.CharField(max_length=100)
    auth_token_label = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_date = models.DateTimeField(auto_now_add=True)
    usage_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Twilio Number: {self.phone_number}, User ID: {self.user.id}, Status: {self.status}"

    def get_fields(self):
        return {
            "user_id": self.user.id,
            "phone_number": self.phone_number,
            "auth_token_label": self.auth_token_label,
            "status": self.status,
            "created_date": self.created_date,
            "usage_count": self.usage_count
        }

    def set_status(self, new_status):
        if new_status in dict(self.STATUS_CHOICES):
            self.status = new_status
            self.save()
            return True
        return False

class AIModel(models.Model):
    
    ai_model_provider = models.CharField(max_length=20)

class AITec(models.Model):

    ai_tec_provider = models.CharField(max_length=20)
class AIAudio(models.Model):

    ai_audio_provider = models.CharField(max_length=20)

class Agent(models.Model):
    name = models.CharField(max_length=100,blank=True, null=True)
    active = models.BooleanField(default=False)
    gender = models.CharField(max_length=20, choices=[('male', 'Male'), ('female', 'Female')], default='male')
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, blank=True, null=True)
    ai_tec = models.ForeignKey(AITec, on_delete=models.CASCADE, blank=True, null=True)
    voice_name = models.ForeignKey(AIAudio, on_delete=models.CASCADE, blank=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agent_details')
    twillio_number = models.ForeignKey(TwilioNumbers, on_delete=models.CASCADE, null=True, blank=True)

    tts_technology_provider = models.ForeignKey(AITec, on_delete=models.CASCADE, related_name='%(class)s_tts_technology_provider', null=True, blank=True)  # Use a unique related_name
    stt_technology_provider = models.ForeignKey(AITec, on_delete=models.CASCADE, related_name='%(class)s_stt_technology_provider', null=True, blank=True)  # Use a unique related_name

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.twillio_number:
            # Using self.__class__ to refer to the specific subclass like FeedbackAgent or SalesAgent
            self.twillio_number.usage_count = self.__class__.objects.filter(
                twillio_number=self.twillio_number).count() + 1
            self.twillio_number.save()
        super().save(*args, **kwargs)



    def __str__(self):
        return f"{self.name} - {'Active' if self.active else 'Inactive'}"

class FeedbackAgent(Agent):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedback_agents', on_delete=models.CASCADE)


class SalesAgent(Agent):
    prompt_files = models.ForeignKey('File', on_delete=models.CASCADE, related_name='%(class)s_prompt_files', null=True, blank=True)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sales_agents', on_delete=models.CASCADE)




class FeedbackQuestion(models.Model):
    order = models.PositiveSmallIntegerField()
    question_text = models.CharField(max_length=255)  # Set an appropriate max_length
    feedback_agent = models.ForeignKey(FeedbackAgent, related_name='feed_questions', on_delete=models.CASCADE)  # Add this line

    def __str__(self):
        return self.question_text
class File(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=100, blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    request_id = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=100, null=True, blank=True)
    last_modified = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    agent_details = models.ForeignKey(SalesAgent, on_delete=models.CASCADE, related_name='agent_details', null=True,blank=True)

    # def __str__(self):
    #     return f"{self.file_name } - {self.agent_details}"

    def __str__(self):
        return f"{self.file_name}"

class AgentFileMapping(models.Model):
    agent_details = models.ForeignKey(SalesAgent, on_delete=models.CASCADE,null=True, blank=True)  # Reference concrete class
    file = models.ForeignKey(File, on_delete=models.CASCADE,null=True, blank=True)
    mapped_date = models.DateTimeField(auto_now_add=True)
