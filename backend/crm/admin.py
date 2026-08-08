from django.contrib import admin
from .models import Opportunity


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        'opportunity_name', 'company_name', 'stage', 'priority',
        'estimated_value', 'currency', 'probability', 'owner', 'is_active',
    )
    list_filter = ('stage', 'priority', 'owner', 'is_active')
    search_fields = ('company_name', 'contact_name', 'opportunity_name')
    list_editable = ('stage', 'priority', 'is_active')
