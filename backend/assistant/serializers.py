from rest_framework import serializers
from .models import Conversation, Message, InteractionLog, SystemPrompt, ResponseEvaluation


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class ConversationListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'message_count', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class InteractionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractionLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class SystemPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemPrompt
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ResponseEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseEvaluation
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField()
    system_prompt_version = serializers.CharField(required=False, allow_blank=True)


class ChatResponseSerializer(serializers.Serializer):
    conversation_id = serializers.CharField()
    user_message = serializers.CharField()
    assistant_response = serializers.CharField()
    tools_used = serializers.ListField(child=serializers.DictField(), default=[])
    rag_context_used = serializers.BooleanField(default=False)
    hallucination_check = serializers.DictField(default={})
    tokens_used = serializers.IntegerField(default=0)
