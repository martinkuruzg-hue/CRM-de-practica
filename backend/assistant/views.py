import json
import time
from datetime import datetime

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Conversation, Message, InteractionLog, SystemPrompt, ResponseEvaluation
from .serializers import (
    ConversationSerializer, ConversationListSerializer,
    MessageSerializer, InteractionLogSerializer,
    SystemPromptSerializer, ResponseEvaluationSerializer,
    ChatRequestSerializer,
)
from .services.memory import ConversationMemory
from .services.rag import RAGService
from .services.tool_registry import ToolRegistry
from .services.hallucination import HallucinationController
from .services.llm import get_llm


memory = ConversationMemory()
rag = RAGService()
tools = ToolRegistry()
hc = HallucinationController()


def get_active_system_prompt(version=None):
    if version:
        prompt = SystemPrompt.objects.filter(version=version).first()
        if prompt:
            return prompt
    prompt = SystemPrompt.objects.filter(is_active=True).first()
    if prompt:
        return prompt
    return SystemPrompt.objects.first()


SYSTEM_PROMPT_TEMPLATE = """Eres un asistente experto en CRM especializado en la gestión de oportunidades de venta.

Tus capacidades:
1. Buscar y consultar oportunidades en el CRM
2. Obtener detalles completos de oportunidades
3. Actualizar el estado de oportunidades
4. Proporcionar resúmenes y análisis del pipeline

Siempre debes:
- Usar las herramientas disponibles cuando sea relevante
- Basar tus respuestas en datos reales del CRM
- Indicar claramente cuando no tienes información suficiente
- Ser conciso y profesional

Contexto actual:
{rag_context}

Historial relevante:
{history_summary}"""


@api_view(['POST'])
def chat(request):
    ser = ChatRequestSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    user_message = ser.validated_data['message']
    conversation_id = ser.validated_data.get('conversation_id', '')
    prompt_version = ser.validated_data.get('system_prompt_version', '')
    start_time = time.time()

    conv = memory.get_or_create_conversation(conversation_id)
    system_prompt_obj = get_active_system_prompt(prompt_version)
    system_content = system_prompt_obj.content if system_prompt_obj else SYSTEM_PROMPT_TEMPLATE

    memory.add_message(conv, 'user', user_message)

    rag_results = rag.search(user_message)
    rag_context = rag.format_context(rag_results)
    hc.set_source_context(rag_context)

    history = memory.get_history(conv)
    history_formatted = memory.format_history_for_llm(history)

    tool_defs = tools.get_tool_definitions()
    llm = get_llm()

    system_content_rendered = system_content.replace(
        '{rag_context}', rag_context or 'No hay contexto adicional disponible.'
    ).replace(
        '{history_summary}',
        f"Esta es la conversación número {history_formatted[-1]['content'][:100] if history_formatted else 'nueva'}."
    )

    messages_for_llm = [{'role': 'system', 'content': system_content_rendered}]
    messages_for_llm.extend(history_formatted[:-1] if history_formatted else [])
    messages_for_llm.append({'role': 'user', 'content': user_message})

    llm_response, tool_calls, tokens_used = llm.chat(messages_for_llm, tools=tool_defs)

    tools_used_info = []
    if tool_calls:
        tool_results_messages = []
        for tc in tool_calls:
            fn_name = tc['function']['name']
            fn_args = tc['function']['arguments']
            result = tools.execute(fn_name, fn_args)

            memory.add_message(conv, 'assistant', '', tool_name=fn_name, tool_arguments=fn_args)
            memory.add_message(conv, 'tool', result, tool_name=fn_name, tool_result=result)

            tool_results_messages.append({
                'role': 'tool',
                'content': result,
                'name': fn_name,
            })
            tools_used_info.append({
                'name': fn_name,
                'arguments': fn_args,
            })

            hc.set_source_context(rag_context, [result])

        messages_for_llm_tools = messages_for_llm.copy()
        messages_for_llm_tools.append({
            'role': 'assistant',
            'content': None,
            'tool_calls': [
                {
                    'id': tc['id'],
                    'type': 'function',
                    'function': {
                        'name': tc['function']['name'],
                        'arguments': tc['function']['arguments'],
                    },
                }
                for tc in tool_calls
            ],
        })
        messages_for_llm_tools.extend(tool_results_messages)

        llm_response2, _, tokens2 = llm.chat(messages_for_llm_tools)
        tokens_used += tokens2
        if llm_response2:
            llm_response = llm_response2

    if not llm_response:
        llm_response = "I can help you manage your CRM opportunities. What would you like to know?"

    hallucination_check = hc.evaluate(llm_response, rag_context, [t['arguments'] for t in tools_used_info])
    if hallucination_check['warnings']:
        llm_response = hc.add_hallucination_guard(llm_response)

    memory.add_message(conv, 'assistant', llm_response)

    if not conv.title and len(user_message) > 10:
        conv.title = user_message[:80] + ('...' if len(user_message) > 80 else '')
        conv.save()

    latency = int((time.time() - start_time) * 1000)
    InteractionLog.objects.create(
        conversation=conv,
        user_message=user_message,
        assistant_response=llm_response,
        tools_used=tools_used_info,
        tokens_used=tokens_used or 0,
        latency_ms=latency,
        system_prompt_version=system_prompt_obj.version if system_prompt_obj else 'default',
        rag_context_used=bool(rag_results),
        hallucination_score=hallucination_check.get('score'),
    )

    return Response({
        'conversation_id': conv.id,
        'user_message': user_message,
        'assistant_response': llm_response,
        'tools_used': tools_used_info,
        'rag_context_used': bool(rag_results),
        'hallucination_check': hallucination_check,
        'tokens_used': tokens_used or 0,
        'latency_ms': latency,
    })


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

    def get_queryset(self):
        conv_id = self.request.query_params.get('conversation')
        qs = super().get_queryset()
        if conv_id:
            qs = qs.filter(conversation_id=conv_id)
        return qs


class InteractionLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InteractionLog.objects.all()
    serializer_class = InteractionLogSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        conv_id = self.request.query_params.get('conversation')
        if conv_id:
            qs = qs.filter(conversation_id=conv_id)
        return qs


class SystemPromptViewSet(viewsets.ModelViewSet):
    queryset = SystemPrompt.objects.all()
    serializer_class = SystemPromptSerializer


class ResponseEvaluationViewSet(viewsets.ModelViewSet):
    queryset = ResponseEvaluation.objects.all()
    serializer_class = ResponseEvaluationSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['post'])
    def quick(self, request):
        message_id = request.data.get('message_id')
        is_helpful = request.data.get('is_helpful')

        if not message_id or is_helpful is None:
            return Response({'error': 'message_id and is_helpful required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            msg = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

        eval = ResponseEvaluation.objects.create(
            message=msg,
            score=5 if is_helpful else 1,
            is_helpful=is_helpful,
        )
        return Response(ResponseEvaluationSerializer(eval).data)
