import uuid
from django.db import models


class Opportunity(models.Model):
    STAGE_CHOICES = [
        ('prospecting', 'Prospecting'),
        ('qualification', 'Qualification'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('closed_won', 'Closed Won'),
        ('closed_lost', 'Closed Lost'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    opportunity_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    estimated_value = models.FloatField(default=0.0)
    currency = models.CharField(max_length=3, default='USD')
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='prospecting')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    probability = models.FloatField(default=0.0)
    owner = models.CharField(max_length=255, blank=True, default='')
    next_follow_up_date = models.CharField(max_length=10, blank=True, default='')
    last_interaction_summary = models.TextField(blank=True, default='')
    ai_recommendation = models.TextField(blank=True, default='')
    created_at = models.CharField(max_length=19, blank=True, default='')
    updated_at = models.CharField(max_length=19, blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.opportunity_name} - {self.company_name}"
