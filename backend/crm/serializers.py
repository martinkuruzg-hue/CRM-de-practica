from rest_framework import serializers
from .models import Opportunity


class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class OpportunitySummarySerializer(serializers.Serializer):
    total_opportunities = serializers.IntegerField()
    total_pipeline_value = serializers.FloatField()
    won_value = serializers.FloatField()
    by_stage = serializers.DictField()
    by_priority = serializers.DictField()
    by_owner = serializers.DictField()
    follow_up_this_week = serializers.IntegerField()
