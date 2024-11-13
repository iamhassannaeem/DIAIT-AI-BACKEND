from django.conf import settings
from django.db import models
from django.utils import timezone


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

    def save(self, *args, **kwargs):
        if not self.created_date:
            self.created_date = timezone.now()
        super().save(*args, **kwargs)

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
    )
    stt_technology_provider = models.ForeignKey(
        AITec,
        on_delete=models.CASCADE,
        related_name="%(class)s_stt_technology_provider",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

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


class Question(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.PositiveSmallIntegerField()
    question_text = models.CharField(max_length=255)
    status = models.BooleanField(default=True)
    feedback_agent = models.ForeignKey(
        FeedbackAgent,
        related_name="feed_questions",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    sales_agent = models.ForeignKey(
        SalesAgent,
        related_name="sales_questions",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    def __str__(self):

        return f"{self.question_text}- {self.ids}"


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


class Campaign(models.Model):
    TYPE_CHOICES = [
        (1, "Outbound"),
        (2, "Inbound"),
    ]
    Status_CHOICES = [
        (1, "Started"),
        (2, "Not Started"),
        (3, "Completed"),
        (4, "Stop"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="campaigns"
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    campaign_local_datetime = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    status = models.IntegerField(choices=Status_CHOICES, default=2)
    type = models.IntegerField(choices=TYPE_CHOICES, null=True, blank=True)
    task_id = models.CharField(max_length=255, null=True, blank=True)
    feedback_agent = models.ForeignKey(
        FeedbackAgent, null=True, blank=True, on_delete=models.CASCADE
    )
    sales_agent = models.ForeignKey(
        SalesAgent, null=True, blank=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return f"Campaign - {self.agent_name} ({self.get_type_display()})"

    def save(self, *args, **kwargs):
        if self.type == 1 and not self.feedback_agent:
            raise ValueError("FeedbackAgent must be assigned for outbound campaigns.")
        elif self.type == 2 and not self.sales_agent:
            raise ValueError("SalesAgentt must be assigned for inbound campaigns.")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):

        self.calls.all().delete()
        Calllogs.objects.filter(call_detail__campaign=self).delete()
        super().delete(*args, **kwargs)


class CallDetails(models.Model):
    phone_number = models.CharField(max_length=15)
    tag = models.CharField(max_length=50, null=True, blank=True)
    call_start_time = models.DateTimeField(null=True, blank=True)
    call_end_time = models.DateTimeField(null=True, blank=True)
    call_duaration = models.DateTimeField(null=True, blank=True)
    conversation = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    call_cost = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="calls"
    )

    def __str__(self):
        return f"Call - {self.phone_number} ({self.get_status_display()})"


class Calllogs(models.Model):
    SENTIMENT_CHOICES = [
        (1, "Positive"),
        (2, "Neutral"),
        (3, "Negative"),
    ]

    call_detail = models.ForeignKey(CallDetails, on_delete=models.CASCADE)
    feedback_question = models.ForeignKey(Question, on_delete=models.CASCADE)

    answer = models.TextField()
    call_sentiments = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Feedback - {self.call_detail} ({self.get_call_sentiments_display()})"


######strip####
class PaymentMethod(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_methods",
    )
    stripe_payment_method_id = models.CharField(max_length=100, unique=True)
    stripe_customer_id = models.CharField(max_length=255)
    card_brand = models.CharField(max_length=50)
    card_last4 = models.CharField(max_length=4)
    card_exp_month = models.IntegerField()
    card_exp_year = models.IntegerField()
    is_verified = models.BooleanField(default=False)


class UserBalance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="balance"
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def add_balance(self, amount):
        self.balance += amount
        self.save()


class TransactionLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
