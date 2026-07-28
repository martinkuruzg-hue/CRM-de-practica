import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
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

@Injectable({ providedIn: 'root' })
export class CrmService {
  private http = inject(HttpClient);
  private base = '/api';

  getOpportunities(): Observable<Opportunity[]> {
    return this.http.get<Opportunity[]>(`${this.base}/opportunities/`);
  }

  getOpportunity(id: string): Observable<Opportunity> {
    return this.http.get<Opportunity>(`${this.base}/opportunities/${id}/`);
  }

  updateOpportunity(id: string, data: Partial<Opportunity>): Observable<Opportunity> {
    return this.http.patch<Opportunity>(`${this.base}/opportunities/${id}/`, data);
  }
}
