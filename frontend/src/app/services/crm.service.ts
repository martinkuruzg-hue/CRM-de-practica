import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Opportunity {
  id: string;
  company_name: string;
  contact_name: string;
  contact_email: string;
  opportunity_name: string;
  description: string;
  estimated_value: number;
  currency: string;
  stage: string;
  priority: string;
  probability: number;
  owner: string;
  next_follow_up_date: string;
  last_interaction_summary: string;
  ai_recommendation: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface OpportunityFilters {
  stage?: string;
  priority?: string;
  owner?: string;
  search?: string;
  is_active?: boolean;
}

export interface PipelineStats {
  total_opportunities: number;
  total_pipeline_value: number;
  won_value: number;
  follow_up_this_week: number;
  by_stage: Record<string, { count: number; value: number }>;
  by_priority: Record<string, { count: number; value: number }>;
  by_owner: Record<string, { count: number; value: number }>;
}

export const STAGES = ['Lead nuevo', 'Contactado', 'Diagnóstico', 'Propuesta enviada', 'Negociación', 'Ganado', 'Perdido'];
export const PRIORITIES = ['Baja', 'Media', 'Alta', 'Crítica'];
export const CURRENCIES = ['USD', 'COP', 'CLP', 'EUR', 'MXN', 'UF'];

@Injectable({ providedIn: 'root' })
export class CrmService {
  private http = inject(HttpClient);
  private base = '/api/opportunities';

  getOpportunities(filters?: OpportunityFilters): Observable<Opportunity[]> {
    let params = new HttpParams();
    if (filters) {
      if (filters.stage) params = params.set('stage', filters.stage);
      if (filters.priority) params = params.set('priority', filters.priority);
      if (filters.owner) params = params.set('owner', filters.owner);
      if (filters.search) params = params.set('search', filters.search);
      if (filters.is_active !== undefined) params = params.set('is_active', String(filters.is_active));
    }
    return this.http.get<Opportunity[]>(`${this.base}/`, { params });
  }

  getOpportunity(id: string): Observable<Opportunity> {
    return this.http.get<Opportunity>(`${this.base}/${id}/`);
  }

  createOpportunity(data: Partial<Opportunity>): Observable<Opportunity> {
    return this.http.post<Opportunity>(`${this.base}/`, data);
  }

  updateOpportunity(id: string, data: Partial<Opportunity>): Observable<Opportunity> {
    return this.http.patch<Opportunity>(`${this.base}/${id}/`, data);
  }

  deleteOpportunity(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/${id}/`);
  }

  getStats(): Observable<PipelineStats> {
    return this.http.get<PipelineStats>(`${this.base}/stats/`);
  }
}
