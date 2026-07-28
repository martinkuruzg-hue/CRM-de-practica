import json
import os
import time
from typing import Optional


class BaseLLM:
    def chat(self, messages, tools=None):
        raise NotImplementedError


class OpenAIService(BaseLLM):
    def __init__(self, api_key=None, model='gpt-4o-mini'):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY', '')
        self.model = model
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
    def chat(self, messages, tools=None):
        last_user_msg = ''
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_user_msg = msg.get('content', '')
                break

        response = (
            f"I understand you're asking about: '{last_user_msg[:100]}'. "
            f"As an AI assistant for this CRM system, I can help you search opportunities, "
            f"get details, update records, and provide insights. "
            f"How can I assist you further?"
        )
        return response, [], 50


def get_llm():
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if api_key:
        return OpenAIService(api_key=api_key)
    return FallbackLLM()
