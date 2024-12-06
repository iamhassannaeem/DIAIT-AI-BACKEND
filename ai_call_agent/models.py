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


class Provider(models.Model):
    provider_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.provider_name


class ProviderCost(models.Model):
    CATEGORY_CHOICES = [
        ("TTS", "tts"),
        ("STT", "stt"),
        ("LLM", "llm"),
        ("Server", "server"),
    ]
    PROVIDER_TYPE_CHOICES = [
        (1, "Outbound_feedback"),
        (2, "Outbound_sales"),
    ]

    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="costs"
    )
    cost_price = models.DecimalField(max_digits=10, decimal_places=6)
    sell_price = models.DecimalField(max_digits=10, decimal_places=6)
    category = models.CharField(max_length=8, choices=CATEGORY_CHOICES)
    provider_type = models.CharField(
        max_length=8, choices=PROVIDER_TYPE_CHOICES, null=True, blank=True
    )

    def __str__(self):
        return (
            f"{self.provider.provider_name} - {self.get_category_display()} - "
            f"Sell Price: ${self.sell_price} - Type: {self.get_provider_type_display()}"
        )


class AIAudio(models.Model):
    ai_audio_provider = models.CharField(max_length=20)


class Industries(models.Model):
    interest = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ClinicDetails(models.Model):
    agent = models.ForeignKey(
        "Agent", on_delete=models.CASCADE, related_name="appointments"
    )
    clinic_name = models.CharField(max_length=255, blank=True, null=True)
    services = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    timing = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)


class DoctorDetails(models.Model):
    clinic = models.ForeignKey(
        "ClinicDetails", on_delete=models.CASCADE, related_name="doctors"
    )
    name = models.CharField(max_length=255, blank=False, null=False)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    available_timings = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Agent(models.Model):
    AGENT_TYPE_CHOICES = [
        ("feedback", "Feedback Agent"),
        ("sales", "Sales Agent"),
        ("appointment", "Appointment Agent"),
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
    industry = models.ForeignKey(
        Industries, on_delete=models.CASCADE, blank=True, null=True
    )
    workflow = models.TextField(blank=True, null=True)

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
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    tag = models.CharField(max_length=100, null=True, blank=True)

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
        max_digits=18, decimal_places=6, null=True, blank=True
    )
    campaign = models.ForeignKey(
        "Campaign", on_delete=models.CASCADE, related_name="call_logs"
    )
    content = models.JSONField(null=True, blank=True)
    sentiments = models.JSONField(null=True, blank=True)
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL, null=True, blank=True
    )
    call_task_id = models.CharField(max_length=255, null=True, blank=True)
    call_sid = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"CallLog - {self.phone_number} ({self.status})"

    def get_queryset(self):
        user = self.request.user
        campaigns = Campaign.objects.filter(user=user)
        return CallLog.objects.filter(campaign__in=campaigns)


class Costtb(models.Model):
    call_log = models.ForeignKey(
        CallLog, on_delete=models.CASCADE, related_name="provider_costs"
    )
    provider = models.ForeignKey(
        ProviderCost, on_delete=models.CASCADE, related_name="call_costs"
    )
    sell_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.00)
    cost = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return (
            f"{self.provider.provider_name}: sell_cost : {self.sell_cost }, "
            f"Cost: {self.cost}, Total_sell_cost: {self.Total_sell_cost}"
        )
