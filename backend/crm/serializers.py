from rest_framework import serializers
from .models import Opportunity


class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        from datetime import datetime
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        validated_data['created_at'] = now
        validated_data['updated_at'] = now
        return super().create(validated_data)

    def update(self, instance, validated_data):
        from datetime import datetime
        validated_data['updated_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        return super().update(instance, validated_data)
