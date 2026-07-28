import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ChatRequest {
  conversation_id?: string;
  message: string;
  system_prompt_version?: string;
}

export interface ChatResponse {
  conversation_id: string;
  user_message: string;
  assistant_response: string;
  tools_used: any[];
  rag_context_used: boolean;
  hallucination_check: { score: number; warnings: string[]; is_safe: boolean };
  tokens_used: number;
  latency_ms: number;
}

export interface Conversation {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation: string;
  role: string;
  content: string;
  tool_name: string;
  tool_arguments: any;
  tool_result: string;
  created_at: string;
}

export interface InteractionLog {
  id: string;
  conversation: string;
  user_message: string;
  assistant_response: string;
  tools_used: any[];
  tokens_used: number;
  latency_ms: number;
  model_used: string;
  system_prompt_version: string;
  rag_context_used: boolean;
  hallucination_score: number;
  created_at: string;
}

export interface SystemPrompt {
  id: string;
  version: string;
  name: string;
  content: string;
  is_active: boolean;
  changelog: string;
  created_at: string;
  updated_at: string;
}

export interface EvaluationRequest {
  message_id: string;
  is_helpful: boolean;
}

@Injectable({ providedIn: 'root' })
export class ChatService {
  private http = inject(HttpClient);
  private base = '/api/assistant';

  sendMessage(req: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.base}/chat/`, req);
  }

  getConversations(): Observable<Conversation[]> {
    return this.http.get<Conversation[]>(`${this.base}/conversations/`);
  }

  getConversation(id: string): Observable<Conversation> {
    return this.http.get<Conversation>(`${this.base}/conversations/${id}/`);
  }

  getMessages(conversationId: string): Observable<Message[]> {
    return this.http.get<Message[]>(`${this.base}/messages/?conversation=${conversationId}`);
  }

  getLogs(): Observable<InteractionLog[]> {
    return this.http.get<InteractionLog[]>(`${this.base}/logs/`);
  }

  getSystemPrompts(): Observable<SystemPrompt[]> {
    return this.http.get<SystemPrompt[]>(`${this.base}/system-prompts/`);
  }

  submitEvaluation(req: EvaluationRequest): Observable<any> {
    return this.http.post(`${this.base}/evaluations/quick/`, req);
  }
}
