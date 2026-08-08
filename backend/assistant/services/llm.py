import json
import os
import time
from typing import Optional


class BaseLLM:
    def chat(self, messages, tools=None):
        raise NotImplementedError


class OpenAIService(BaseLLM):
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY', '')
        self.model = model or os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def chat(self, messages, tools=None):
        if not self.api_key:
            return None, {'error': 'OpenAI API key not configured'}, 0

        client = self._get_client()
        params = {
            'model': self.model,
            'messages': messages,
            'temperature': 0.3,
        }
        if tools:
            params['tools'] = tools
            params['tool_choice'] = 'auto'

        response = client.chat.completions.create(**params)
        choice = response.choices[0]

        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    'id': tc.id,
                    'type': tc.type,
                    'function': {'name': tc.function.name, 'arguments': tc.function.arguments},
                })

        return choice.message.content, tool_calls, response.usage.total_tokens if response.usage else 0


class FallbackLLM(BaseLLM):
    """Asistente offline (sin API key) basado en reglas.

    Consulta datos reales del CRM a través de las herramientas de negocio y
    compone respuestas legibles a partir de los resultados obtenidos.
    Nunca inventa oportunidades: si no hay datos, lo dice explícitamente.
    """

    def chat(self, messages, tools=None):
        last_user_msg = ''
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_user_msg = msg.get('content', '')
                break

        last_tool_result = None
        for msg in reversed(messages):
            if msg.get('role') == 'tool':
                last_tool_result = msg.get('content', '')
                break

        if last_tool_result:
            return self._compose_from_tool_result(last_tool_result), [], 25

        tool_calls = self._detect_intent(last_user_msg, tools)
        if tool_calls:
            return None, tool_calls, 25

        return self._out_of_scope_response(), [], 25

    def _detect_intent(self, message, tools):
        if not tools:
            return []
        low = message.lower()
        available = {t['function']['name'] for t in tools}

        if any(k in low for k in ('resumen', 'summary', 'pipeline', 'valor total', 'estado del crm')):
            if 'get_crm_summary' in available:
                return [{'id': 'fb-1', 'type': 'function',
                         'function': {'name': 'get_crm_summary', 'arguments': json.dumps({'group_by': 'stage'})}}]

        if any(k in low for k in ('seguimiento', 'semana', 'follow-up', 'follow up', 'recordatori')):
            if 'get_follow_ups' in available:
                return [{'id': 'fb-2', 'type': 'function',
                         'function': {'name': 'get_follow_ups', 'arguments': '{}'}}]

        if any(k in low for k in ('critica', 'crítica', 'prioridad alta', 'urgente')):
            if 'search_opportunities' in available:
                return [{'id': 'fb-3', 'type': 'function',
                         'function': {'name': 'search_opportunities',
                                      'arguments': json.dumps({'query': 'prioridad', 'limit': 10})}}]

        if any(k in low for k in ('negociacion', 'negociación', 'propuesta', 'lead', 'contactado', 'diagnostico', 'diagnóstico')):
            if 'get_crm_summary' in available:
                return [{'id': 'fb-4', 'type': 'function',
                         'function': {'name': 'get_crm_summary', 'arguments': json.dumps({'group_by': 'stage'})}}]

        if any(k in low for k in ('probabilidad', 'cierre', 'cerrar', 'mejores')):
            if 'search_opportunities' in available:
                return [{'id': 'fb-5', 'type': 'function',
                         'function': {'name': 'search_opportunities',
                                      'arguments': json.dumps({'query': 'probabilidad', 'limit': 10})}}]

        if any(k in low for k in ('busca', 'encuentra', 'empresa', 'clientes', 'oportunidades de')):
            if 'search_opportunities' in available:
                return [{'id': 'fb-6', 'type': 'function',
                         'function': {'name': 'search_opportunities',
                                      'arguments': json.dumps({'query': message, 'limit': 10})}}]

        return []

    def _compose_from_tool_result(self, result_text):
        try:
            data = json.loads(result_text)
        except (ValueError, TypeError):
            return self._out_of_scope_response()

        if 'error' in data:
            return (
                "No encontré información suficiente en el CRM para responder. "
                "Puedo ayudarte a consultar oportunidades, resumir el pipeline o listar seguimientos pendientes."
            )

        if 'items' in data and 'window_days' in data:
            if not data['items']:
                return "No hay oportunidades con seguimiento pendiente en los próximos 7 días."
            lines = ["Oportunidades que requieren seguimiento en los próximos 7 días:"]
            for it in data['items']:
                lines.append(
                    f"- {it['company_name']} | {it['opportunity_name']} | "
                    f"Etapa: {it['stage']} | Prioridad: {it['priority']} | "
                    f"Próximo seguimiento: {it['next_follow_up_date']} | Responsable: {it['owner']}"
                )
            return "\n".join(lines)

        if 'groups' in data:
            lines = [
                f"Resumen del CRM: {data['total_opportunities']} oportunidades activas con un valor total estimado de "
                f"${data['total_value']:,.0f} USD."
            ]
            for group, info in sorted(data['groups'].items()):
                lines.append(
                    f"- {group}: {info['count']} oportunidad(es), valor estimado ${info['total_value']:,.0f} USD."
                )
            return "\n".join(lines)

        if 'results' in data:
            results = data.get('results', [])
            if not results:
                return "No encontré oportunidades que coincidan con tu consulta en el CRM."
            lines = ["Resultados encontrados en el CRM:"]
            for r in results:
                lines.append(
                    f"- {r['company_name']} | {r['opportunity_name']} | "
                    f"Etapa: {r['stage']} | Prioridad: {r['priority']} | "
                    f"Probabilidad: {r['probability']}% | Valor: ${r['estimated_value']:,.0f} {r['currency']}"
                )
            return "\n".join(lines)

        return self._out_of_scope_response()

    def _out_of_scope_response(self):
        return (
            "Solo puedo responder preguntas sobre el CRM: oportunidades, etapas, prioridades, "
            "valor del pipeline, seguimientos pendientes y resúmenes del estado comercial. "
            "Ejemplo: '¿Cuáles son las oportunidades con prioridad crítica?'"
        )


def get_llm():
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if api_key:
        return OpenAIService(api_key=api_key)
    return FallbackLLM()
