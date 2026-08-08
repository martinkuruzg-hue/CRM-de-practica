import uuid
from django.db import models


class Opportunity(models.Model):
    STAGE_CHOICES = [
        ('Lead nuevo', 'Lead nuevo'),
        ('Contactado', 'Contactado'),
        ('Diagnóstico', 'Diagnóstico'),
        ('Propuesta enviada', 'Propuesta enviada'),
        ('Negociación', 'Negociación'),
        ('Ganado', 'Ganado'),
        ('Perdido', 'Perdido'),
    ]
    PRIORITY_CHOICES = [
        ('Baja', 'Baja'),
        ('Media', 'Media'),
        ('Alta', 'Alta'),
        ('Crítica', 'Crítica'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    opportunity_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    estimated_value = models.FloatField(default=0.0)
    currency = models.CharField(max_length=10, default='USD')
    stage = models.CharField(max_length=30, choices=STAGE_CHOICES, default='Lead nuevo')
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default='Media')
    probability = models.IntegerField(default=0)
    owner = models.CharField(max_length=255, blank=True, default='')
    next_follow_up_date = models.DateField(null=True, blank=True)
    last_interaction_summary = models.TextField(blank=True, default='')
    ai_recommendation = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.opportunity_name} - {self.company_name}"
