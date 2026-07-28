import uuid
from django.db import models


class Conversation(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f"Conversation {self.id[:8]}"


class Message(models.Model):
    ROLE_CHOICES = [
        ('system', 'System'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('tool', 'Tool'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField(blank=True, default='')
    tool_name = models.CharField(max_length=100, blank=True, default='')
    tool_arguments = models.JSONField(null=True, blank=True)
    tool_result = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"


class InteractionLog(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    user_message = models.TextField()
    assistant_response = models.TextField(blank=True, default='')
    tools_used = models.JSONField(null=True, blank=True, default=list)
    tokens_used = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    model_used = models.CharField(max_length=100, blank=True, default='')
    system_prompt_version = models.CharField(max_length=20, blank=True, default='')
    rag_context_used = models.BooleanField(default=False)
    hallucination_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Log {self.id[:8]} - {self.created_at}"


class SystemPrompt(models.Model):
    version = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255, blank=True, default='')
    content = models.TextField()
    is_active = models.BooleanField(default=False)
    changelog = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"v{self.version}: {self.name}"


class ResponseEvaluation(models.Model):
    SCORE_CHOICES = [(i, str(i)) for i in range(1, 6)]

    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='evaluations')
    score = models.IntegerField(choices=SCORE_CHOICES)
    feedback = models.TextField(blank=True, default='')
    is_helpful = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Evaluation {self.id[:8]} - Score: {self.score}"
