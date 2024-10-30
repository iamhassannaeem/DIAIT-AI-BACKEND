from django.db import models
from django.conf import settings
from pytz import common_timezones


class TwilioNumbers(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    account_sid = models.CharField(max_length=100)
    account_auth_token = models.CharField(max_length=100)
    auth_token_label = models.CharField(max_length=100)
    account_api_secret = models.CharField(max_length=100)
    account_api_sid = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    created_date = models.DateTimeField(auto_now_add=True)
    usage_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Twilio Number: {self.phone_number},Twilio id: {self.id}, User ID: {self.user.id}, Status: {self.status}"

    def get_fields(self):
        return {
            "user_id": self.user.id,
            "phone_number": self.phone_number,
            "auth_token_label": self.auth_token_label,
            "status": self.status,
            "created_date": self.created_date,
            "usage_count": self.usage_count,
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
    first_message = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=False)
    gender = models.CharField(
        max_length=20, choices=[("male", "Male"), ("female", "Female")], default="male"
    )
    ai_model = models.ForeignKey(
        AIModel, on_delete=models.CASCADE, blank=True, null=True
    )
    ai_tec = models.ForeignKey(AITec, on_delete=models.CASCADE, blank=True, null=True)
    voice_name = models.ForeignKey(
        AIAudio, on_delete=models.CASCADE, blank=True, null=True
    )
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_details"
    )
    twillio_number = models.ForeignKey(
        TwilioNumbers, on_delete=models.CASCADE, null=True, blank=True
    )

    tts_technology_provider = models.ForeignKey(
        AITec,
        on_delete=models.CASCADE,
        related_name="%(class)s_tts_technology_provider",
        null=True,
        blank=True,
    )  # Use a unique related_name
    stt_technology_provider = models.ForeignKey(
        AITec,
        on_delete=models.CASCADE,
        related_name="%(class)s_stt_technology_provider",
        null=True,
        blank=True,
    )  # Use a unique related_name

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.twillio_number:
            # Using self.__class__ to refer to the specific subclass like FeedbackAgent or SalesAgent
            self.twillio_number.usage_count = (
                self.__class__.objects.filter(
                    twillio_number=self.twillio_number
                ).count()
                + 1
            )
            self.twillio_number.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {'Active' if self.active else 'Inactive'}"


class FeedbackAgent(Agent):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="feedback_agents",
        on_delete=models.CASCADE,
    )


class SalesAgent(Agent):
    pass


class FeedbackQuestion(models.Model):
    order = models.PositiveSmallIntegerField()
    question_text = models.CharField(max_length=255)  # Set an appropriate max_length
    feedback_agent = models.ForeignKey(
        FeedbackAgent, related_name="feed_questions", on_delete=models.CASCADE
    )  # Add this line

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
    agent_details = models.ForeignKey(
        SalesAgent,
        on_delete=models.CASCADE,
        related_name="agent_details",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.file_name}- {self.created_date}"


class AgentFileMapping(models.Model):
    FILE_TYPE_CHOICES = [
        ("prompt_files", "Prompt Files"),
        ("product_pricing", "Product Pricing"),
        ("pricing", "Pricing"),
        ("general_information", "General Information"),
        ("product_information", "Product Information"),
        ("company_information", "Company Information"),
    ]

    agent_details = models.ForeignKey(
        SalesAgent, on_delete=models.CASCADE, null=True, blank=True
    )
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True, blank=True)
    mapped_date = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=30, choices=FILE_TYPE_CHOICES)

    def __str__(self):
        return f"{self.file} mapped as {self.get_file_type_display()} for {self.agent_details}"


class CampaignNumberList(models.Model):
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.phone_number


class OutboundCampaign(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
    ]

    feedback_agent = models.ForeignKey(
        "FeedbackAgent", on_delete=models.CASCADE, related_name="outbound_campaigns"
    )
    name = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    time_zone = models.CharField(
        max_length=50, choices=[(tz, tz) for tz in common_timezones]
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="scheduled"
    )
    number_list = models.ManyToManyField(CampaignNumberList, related_name="campaigns")

    def __str__(self):
        return f"Campaign: {self.name}, Status: {self.status}"

    def get_number_count(self):
        return self.number_list.count()
