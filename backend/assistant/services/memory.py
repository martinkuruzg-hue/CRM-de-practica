from ..models import Conversation, Message


class ConversationMemory:
    def get_or_create_conversation(self, conversation_id=None):
        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                pass
        return Conversation.objects.create()

    def get_history(self, conversation, limit=20):
        messages = Message.objects.filter(conversation=conversation).order_by('-created_at')
        if limit:
            messages = messages[:limit]
        return list(reversed(messages))

    def add_message(self, conversation, role, content, tool_name='', tool_arguments=None, tool_result=''):
        return Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            tool_result=tool_result,
        )

    def format_history_for_llm(self, messages):
        formatted = []
        for msg in messages:
            entry = {'role': msg.role, 'content': msg.content}
            if msg.role == 'tool':
                entry['name'] = msg.tool_name
            formatted.append(entry)
        return formatted

    def clear_conversation(self, conversation):
        Message.objects.filter(conversation=conversation).delete()
