from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


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
        return f"Twilio Number: {self.phone_number}, Status: {self.status}"


class AIModel(models.Model):

    ai_model_provider = models.CharField(max_length=20)


class AITec(models.Model):

    ai_tec_provider = models.CharField(max_length=20)


class AIAudio(models.Model):

    ai_audio_provider = models.CharField(max_length=20)


class Agent(models.Model):
    AGENT_TYPE_CHOICES = [
        ("feedback", "Feedback Agent"),
        ("sales", "Sales Agent"),
    ]
    first_message = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=False)
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPE_CHOICES)
    gender = models.CharField(
        max_length=20,
        choices=[("male", "Male"), ("female", "Female")],
        blank=True,
        null=True,
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
    )
    stt_technology_provider = models.ForeignKey(
        AITec,
        on_delete=models.CASCADE,
        related_name="%(class)s_stt_technology_provider",
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.twillio_number:
            self.twillio_number.usage_count = (
                self.__class__.objects.filter(
                    twillio_number=self.twillio_number
                ).count()
                + 1
            )
            self.twillio_number.save()

        super().save(*args, **kwargs)


class Question(models.Model):
    order = models.PositiveSmallIntegerField()
    question_text = models.CharField(max_length=255)
    status = models.BooleanField(default=True)
    agent = models.ForeignKey(
        Agent,
        related_name="questions",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.question_text}"


class File(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=100, blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    request_id = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=100, null=True, blank=True)
    last_modified = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    s3_key = models.CharField(max_length=255, blank=True, null=True)
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name="files",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.file_name} - {self.created_date}"


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
        "Agent",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    file = models.ForeignKey(
        "File",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    mapped_date = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=30, choices=FILE_TYPE_CHOICES)

    def __str__(self):
        return f"{self.file} mapped as {self.get_file_type_display()} for {self.agent_details}"

    def clean(self):
        if self.agent_details and self.agent_details.agent_type != "sales":
            raise ValidationError("File mapping can only be applied to Sales agents.")
        super().clean()


class Campaign(models.Model):
    TYPE_CHOICES = [
        (1, "Outbound_feedback"),
        (2, "Outbound_sales"),
    ]
    STATUS_CHOICES = [
        (1, "Started"),
        (2, "Not Started"),
        (3, "Completed"),
        (4, "Stopped"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="campaigns"
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    campaign_local_datetime = models.DateTimeField(null=True, blank=True)
    campaign_completed_datetime = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    type = models.IntegerField(choices=TYPE_CHOICES, null=True, blank=True)
    task_id = models.CharField(max_length=255, null=True, blank=True)

    status = models.IntegerField(choices=STATUS_CHOICES, default=2)
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="campaigns",
    )

    def __str__(self):
        return f"Campaign - {self.name} ({self.get_type_display()})"


class Contact(models.Model):
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.phone_number


class CallLog(models.Model):
    phone_number = models.CharField(max_length=15)
    tag = models.CharField(max_length=50, null=True, blank=True)
    call_start_time = models.DateTimeField(null=True, blank=True)
    call_end_time = models.DateTimeField(null=True, blank=True)
    call_duration = models.DurationField(null=True, blank=True)
    conversation = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    call_cost = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    campaign = models.ForeignKey(
        "Campaign", on_delete=models.CASCADE, related_name="call_logs"
    )
    content = models.JSONField(null=True, blank=True)
    sentiments = models.JSONField(null=True, blank=True)
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"CallLog - {self.phone_number} ({self.status})"


# class CallDetails(models.Model):
#     phone_number = models.CharField(max_length=15)
#     tag = models.CharField(max_length=50, null=True, blank=True)
#     call_start_time = models.DateTimeField(null=True, blank=True)
#     call_end_time = models.DateTimeField(null=True, blank=True)
#     call_duaration = models.DateTimeField(null=True, blank=True)
#     conversation = models.TextField(null=True, blank=True)
#     status = models.TextField(null=True, blank=True)
#     call_cost = models.DecimalField(
#         max_digits=18, decimal_places=2, null=True, blank=True
#     )
#     campaign = models.ForeignKey(
#         Campaign, on_delete=models.CASCADE, related_name="calls"
#     )
#
#     def __str__(self):
#         return f"Call - {self.phone_number} ({self.get_status_display()})"


# class CallLog(models.Model):
#
#     call_detail = models.ForeignKey(CallDetails, on_delete=models.CASCADE)
#     question = models.ForeignKey(Question, on_delete=models.CASCADE)
#     answer = models.TextField()
#     call_sentiments = models.TextField(null=True, blank=True)
#
#     def __str__(self):
#         return f"Feedback - {self.call_detail}"
